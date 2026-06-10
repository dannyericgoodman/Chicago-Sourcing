import Anthropic from "@anthropic-ai/sdk";

// Ported from vc_reading/summarize.py — same JSON shape and anti-hallucination
// guard, generalized from "investor angle" to a single "key insight" so it works
// for any newsletter or blog, not just the VC canon.

export type Summary = {
  one_liner: string;
  takeaways: string[];
  key_insight: string;
};

const SHAPE = `Respond with ONLY a JSON object, no prose around it, in exactly this shape:
{
  "one_liner": "<one sentence: the single core idea>",
  "takeaways": ["<3 to 5 crisp, specific takeaways; each one sentence; favor durable ideas and concrete specifics over generic summary>"],
  "key_insight": "<one sentence on the most useful or non-obvious thing to remember>"
}`;

function prompt(title: string, source: string, text: string): string {
  return `You distill writing for a busy, smart reader who has ~20 seconds per piece. Below is a post titled "${title}" from "${source}".

Read it and distill it. ${SHAPE}

POST:
---
${text.slice(0, 16000)}
---`;
}

function modelChain(): string[] {
  const chain = [process.env.SKIM_MODEL, "claude-haiku-4-5-20251001", "claude-sonnet-4-6"];
  return [...new Set(chain.filter(Boolean) as string[])];
}

function parse(raw: string): Summary | null {
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start === -1 || end === -1) return null;
  try {
    const obj = JSON.parse(raw.slice(start, end + 1));
    const takeaways = Array.isArray(obj.takeaways)
      ? obj.takeaways.filter((t: unknown) => typeof t === "string" && t.trim()).slice(0, 5)
      : [];
    if (!obj.one_liner || takeaways.length === 0) return null;
    return {
      one_liner: String(obj.one_liner).trim(),
      takeaways,
      key_insight: String(obj.key_insight || "").trim(),
    };
  } catch {
    return null;
  }
}

export async function summarize(title: string, source: string, text: string): Promise<Summary | null> {
  if (!text || text.trim().length < 200) return null; // not enough to summarize honestly
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  for (const model of modelChain()) {
    try {
      const resp = await client.messages.create({
        model,
        max_tokens: 700,
        messages: [{ role: "user", content: prompt(title, source, text) }],
      });
      const block = resp.content.find((b) => b.type === "text");
      const out = block && block.type === "text" ? parse(block.text) : null;
      if (out) return out;
    } catch (err) {
      console.warn(`summarize: model ${model} failed:`, (err as Error).message);
    }
  }
  return null;
}
