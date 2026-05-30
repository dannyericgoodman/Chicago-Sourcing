"""Generate study-oriented takeaways for an essay using Claude.

Two paths:
* Full-text — when we successfully fetched the essay, summarize the text.
* Knowledge-based — when the source site blocked the fetch (notably Gurley's
  abovethecrowd.com on CI), ask the model to summarize the *known* canonical
  essay from the title/author, with an explicit guard: if it isn't confident it
  knows the specific piece, it returns empty so we don't fabricate takeaways.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)


def _model_chain() -> List[str]:
    """Models tried in order. Opus 4.8 first (the user's choice); fall back to a
    model the repo already calls successfully so one bad model ID can't blank
    every summary."""
    chain = []
    if os.getenv("VC_MODEL"):
        chain.append(os.getenv("VC_MODEL"))
    chain += ["claude-opus-4-8", "claude-sonnet-4-20250514"]
    seen, out = set(), []
    for m in chain:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


_SHAPE = """Respond with ONLY a JSON object, no prose around it, in exactly this shape:
{{
  "one_liner": "<one sentence: the single core idea>",
  "takeaways": [
    "<3 to 5 crisp, specific takeaways; each one sentence; favor durable mental \
models and investor-relevant judgment over surface summary>"
  ],
  "investor_angle": "<one sentence on why this matters for an early-stage VC's \
decision-making or founder evaluation>"
}}"""

PROMPT_TEXT = """You are a mentor helping an aspiring elite early-stage venture \
capitalist study the canon. Below is an essay by {author}, titled "{title}".

Read it and distill it for a busy investor. """ + _SHAPE + """

ESSAY:
---
{text}
---"""

PROMPT_KNOWLEDGE = """You are a mentor helping an aspiring elite early-stage \
venture capitalist study the canon. Summarize the well-known essay "{title}" by \
{author} from your own knowledge of it.

IMPORTANT: Only do this if you are genuinely confident you know this specific \
essay. If you are not sure which essay this is, return {{"one_liner": "", \
"takeaways": [], "investor_angle": ""}} and nothing else — do NOT guess or \
fabricate.

""" + _SHAPE


def _fallback(title: str, reason: str) -> Dict:
    return {
        "one_liner": f"Classic essay: {title}.",
        "takeaways": [
            f"Auto-summary unavailable this run ({reason}) — read it directly "
            "via the link below."
        ],
        "investor_angle": "Part of the early-stage VC canon worth reading in full.",
        "ok": False,
    }


def _parse(raw: str, title: str) -> Dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(match.group(0) if match else raw)
    takeaways = data.get("takeaways") or []
    if isinstance(takeaways, str):
        takeaways = [takeaways]
    return {
        "one_liner": str(data.get("one_liner", "")).strip(),
        "takeaways": [str(t).strip() for t in takeaways if str(t).strip()],
        "investor_angle": str(data.get("investor_angle", "")).strip(),
        "ok": True,
    }


def summarize(author_name: str, title: str, text: Optional[str], url: str,
              client: Optional[Anthropic] = None) -> Dict:
    """Return {one_liner, takeaways[list], investor_angle, ok}. Never raises."""
    if not os.getenv("ANTHROPIC_API_KEY") and client is None:
        return _fallback(title, "ANTHROPIC_API_KEY not set")

    if text:
        prompt = PROMPT_TEXT.format(author=author_name, title=title, text=text)
        mode = "full-text"
    else:
        logger.warning("No fetched text for '%s' — summarizing from knowledge.", title)
        prompt = PROMPT_KNOWLEDGE.format(author=author_name, title=title)
        mode = "knowledge"

    client = client or Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    last_err = None
    for model in _model_chain():
        try:
            resp = client.messages.create(
                model=model, max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            result = _parse(resp.content[0].text, title)
            if result["takeaways"]:
                logger.info("Summarized '%s' (%s, %s).", title, mode, model)
                return result
            last_err = "model returned empty (likely unknown essay)"
        except Exception as exc:
            last_err = str(exc)
            logger.warning("Model %s failed for '%s': %s", model, title, exc)
            continue
    logger.error("Summary failed for '%s': %s", title, last_err)
    return _fallback(title, "fetch blocked & essay not recognized"
                     if mode == "knowledge" else "model call failed")
