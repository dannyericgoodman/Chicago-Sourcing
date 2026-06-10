import Parser from "rss-parser";
import * as cheerio from "cheerio";

const parser = new Parser({
  timeout: 20000,
  headers: { "User-Agent": "SkimBot/0.1 (+https://github.com; newsletter stories)" },
  customFields: { item: [["content:encoded", "contentEncoded"]] },
});

export type FeedItem = {
  guid: string;
  title: string;
  url: string;
  author: string | null;
  publishedAt: string | null;
  // Best-effort plain text of the post, for summarizing.
  text: string;
};

export type Feed = { title: string; siteUrl: string | null; items: FeedItem[] };

function strip(html: string | undefined): string {
  if (!html) return "";
  const $ = cheerio.load(html);
  $("script, style").remove();
  return $.text().replace(/\s+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/[ \t]{2,}/g, " ").trim();
}

// Lightweight: read feed metadata + any inline body. We deliberately do NOT
// fetch each article here — the summarize step pulls full text only for posts
// that are actually new and inside the window, so ingest stays fast.
export async function parseFeed(feedUrl: string): Promise<Feed> {
  const feed = await parser.parseURL(feedUrl);
  const items: FeedItem[] = [];
  for (const e of feed.items) {
    const url = e.link || "";
    if (!url) continue;
    const text = strip((e as any).contentEncoded || e.content || e.contentSnippet);
    items.push({
      guid: e.guid || (e as any).id || url,
      title: (e.title || "Untitled").trim(),
      url,
      author: (e as any).creator || (e as any).author || feed.title || null,
      publishedAt: e.isoDate || (e.pubDate ? new Date(e.pubDate).toISOString() : null),
      text,
    });
  }
  return { title: feed.title || feedUrl, siteUrl: feed.link || null, items };
}

// Turn a pasted blog/Substack/Ghost URL into its RSS feed. Tries the URL as a
// feed first, then common conventions, then <link rel=alternate> autodiscovery.
export async function discoverFeed(input: string): Promise<{ feedUrl: string; title: string; siteUrl: string | null } | null> {
  const url = input.trim().replace(/\/+$/, "");
  const candidates = [url, `${url}/feed`, `${url}/rss`, `${url}/feed.xml`, `${url}/rss.xml`, `${url}/atom.xml`];

  for (const c of candidates) {
    try {
      const f = await parser.parseURL(c);
      if (f.items?.length) return { feedUrl: c, title: f.title || c, siteUrl: f.link || url };
    } catch {
      /* try next */
    }
  }

  try {
    const res = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 SkimBot/0.1" }, signal: AbortSignal.timeout(15000) });
    if (res.ok) {
      const $ = cheerio.load(await res.text());
      const href =
        $('link[rel="alternate"][type="application/rss+xml"]').attr("href") ||
        $('link[rel="alternate"][type="application/atom+xml"]').attr("href");
      if (href) {
        const feedUrl = new URL(href, url).toString();
        const f = await parser.parseURL(feedUrl);
        return { feedUrl, title: f.title || url, siteUrl: f.link || url };
      }
    }
  } catch {
    /* fall through */
  }
  return null;
}
