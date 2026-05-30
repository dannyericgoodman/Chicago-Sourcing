"""Generate study-oriented takeaways for an essay using Claude."""

import json
import logging
import os
import re
from typing import Dict, List, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Models tried in order. Opus 4.8 first (the user's choice); if the account/key
# can't use it, fall back to a model the repo is already known to call
# successfully so a single bad model ID can't silently blank every summary.
def _model_chain() -> List[str]:
    chain = []
    if os.getenv("VC_MODEL"):
        chain.append(os.getenv("VC_MODEL"))
    chain += ["claude-opus-4-8", "claude-sonnet-4-20250514"]
    # de-dupe, preserve order
    seen, out = set(), []
    for m in chain:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


PROMPT = """You are a mentor helping an aspiring elite early-stage venture \
capitalist study the canon. Below is an essay by {author}, titled "{title}".

Read it and distill it for a busy investor. Respond with ONLY a JSON object, no \
prose around it, in exactly this shape:

{{
  "one_liner": "<one sentence: the single core idea>",
  "takeaways": [
    "<3 to 5 crisp, specific takeaways; each one sentence; favor durable mental \
models and investor-relevant judgment over surface summary>"
  ],
  "investor_angle": "<one sentence on why this matters for an early-stage VC's \
decision-making or founder evaluation>"
}}

ESSAY:
---
{text}
---"""


def _fallback(title: str, reason: str) -> Dict:
    return {
        "one_liner": f"Classic essay: {title}.",
        "takeaways": [
            f"Auto-summary unavailable this run ({reason}) — read it directly "
            "via the link below."
        ],
        "investor_angle": "Part of the early-stage VC canon worth reading in full.",
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
        "one_liner": str(data.get("one_liner", title)).strip(),
        "takeaways": [str(t).strip() for t in takeaways if str(t).strip()],
        "investor_angle": str(data.get("investor_angle", "")).strip(),
    }


def summarize(author_name: str, title: str, text: Optional[str], url: str,
              client: Optional[Anthropic] = None) -> Dict:
    """Return {one_liner, takeaways[list], investor_angle}. Never raises."""
    if not text:
        logger.warning("No article text for '%s' — fetch likely failed.", title)
        return _fallback(title, "couldn't fetch full text")

    if not os.getenv("ANTHROPIC_API_KEY") and client is None:
        return _fallback(title, "ANTHROPIC_API_KEY not set")

    client = client or Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    last_err = None
    for model in _model_chain():
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": PROMPT.format(author=author_name, title=title, text=text),
                }],
            )
            result = _parse(resp.content[0].text, title)
            if result["takeaways"]:
                logger.info("Summarized '%s' with %s.", title, model)
                return result
            last_err = "empty takeaways"
        except Exception as exc:
            last_err = str(exc)
            logger.warning("Model %s failed for '%s': %s", model, title, exc)
            continue
    logger.error("All models failed for '%s': %s", title, last_err)
    return _fallback(title, "model call failed")
