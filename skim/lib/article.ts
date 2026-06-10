import * as cheerio from "cheerio";

// Best-effort plain text of a single article URL, for summarizing.
export async function parseArticleText(url: string): Promise<string> {
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0 SkimBot/0.1" },
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) return "";
    const $ = cheerio.load(await res.text());
    $("script, style, nav, header, footer, aside, form").remove();
    const main = $("article").first().text() || $("main").first().text() || $("body").text();
    return main.replace(/\n{3,}/g, "\n\n").replace(/[ \t]{2,}/g, " ").trim().slice(0, 16000);
  } catch {
    return "";
  }
}
