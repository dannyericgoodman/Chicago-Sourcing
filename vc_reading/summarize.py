"""Generate study-oriented takeaways for an essay using Claude."""

import json
import logging
import os
import re
from typing import Dict, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Opus 4.8 by default (user's choice); override with VC_MODEL if desired.
DEFAULT_MODEL = os.getenv("VC_MODEL", "claude-opus-4-8")

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


def _fallback(title: str, url: str) -> Dict:
    return {
        "one_liner": f"Classic essay: {title}.",
        "takeaways": [
            "Full text could not be summarized automatically this run — "
            "read it directly via the link below."
        ],
        "investor_angle": "Part of the early-stage VC canon worth reading in full.",
    }


def summarize(author_name: str, title: str, text: Optional[str], url: str,
              client: Optional[Anthropic] = None, model: str = DEFAULT_MODEL) -> Dict:
    """Return {one_liner, takeaways[list], investor_angle}. Never raises."""
    if not text:
        return _fallback(title, url)

    client = client or Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": PROMPT.format(author=author_name, title=title, text=text),
            }],
        )
        raw = resp.content[0].text.strip()
        # Strip markdown fences if the model wrapped the JSON.
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
    except Exception as exc:
        logger.error("Summarization failed for '%s': %s", title, exc)
        return _fallback(title, url)
