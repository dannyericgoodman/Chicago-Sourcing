import Parser from "rss-parser";
import * as cheerio from "cheerio";

const UA = "Mozilla/5.0 (compatible; SkimBot/0.1; +newsletter stories)";

const parser = new Parser({
  timeout: 20000,
  headers: { "User-Agent": UA },
  customFields: { item: [["content:encoded", "contentEncoded"]] },
});

export type FeedItem = {
  guid: string;
  title: string;
  url: string;
  author: string | null;
  publishedAt: string | null;
  text: string; // best-effort inline body; summarize step fetches full text
};

export type Feed = { title: string; siteUrl: string | null; items: FeedItem[] };

// How a source is polled. "rss" parses a feed; "scrape" diffs a homepage's
// article links when no feed exists at all.
export type SourceKind = "rss" | "scrape";

export type Discovered = {
  kind: SourceKind;
  // The URL we poll on each ingest (a feed URL for rss, the page URL for scrape).
  pollUrl: string;
  title: string;
  siteUrl: string | null;
};

function strip(html: string | undefined): string {
  if (!html) return "";
  const $ = cheerio.load(html);
  $("script, style").remove();
  return $.text().replace(/\s+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/[ \t]{2,}/g, " ").trim();
}

async function getHtml(url: string): Promise<string | null> {
  try {
    const res = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(15000) });
    return res.ok ? await res.text() : null;
  } catch {
    return null;
  }
}

async function tryFeed(url: string): Promise<Discovered | null> {
  try {
    const f = await parser.parseURL(url);
    if (f.items?.length) return { kind: "rss", pollUrl: url, title: f.title || url, siteUrl: f.link || null };
  } catch {
    /* not a feed */
  }
  return null;
}

// ----- Tier 1: platform-specific feed URLs (the common content homes) -----
async function platformCandidates(input: string): Promise<string[]> {
  let u: URL;
  try {
    u = new URL(input);
  } catch {
    return [];
  }
  const host = u.hostname.replace(/^www\./, "");
  const path = u.pathname.replace(/\/+$/, "");
  const out: string[] = [];

  if (host.endsWith("substack.com")) out.push(`${u.origin}/feed`);
  if (host === "medium.com") {
    if (path.startsWith("/@")) out.push(`https://medium.com/feed${path}`);
    else if (path) out.push(`https://medium.com/feed${path}`);
  }
  if (host.endsWith("medium.com") && host !== "medium.com") out.push(`${u.origin}/feed`); // pub.medium.com style
  if (host === "youtube.com" || host === "m.youtube.com") {
    const m = path.match(/\/channel\/([\w-]+)/);
    if (m) out.push(`https://www.youtube.com/feeds/videos.xml?channel_id=${m[1]}`);
    // /@handle and /c/name need the channelId resolved from the page (handled in autodiscovery).
  }
  if (host === "reddit.com" || host === "old.reddit.com") out.push(`${u.origin}${path}/.rss`);
  if (host === "github.com" && path) out.push(`${u.origin}${path}.atom`); // releases/commits feeds
  return out;
}

// ----- Tier 2: <link rel=alternate> autodiscovery + inline feed links -----
async function autodiscover(input: string): Promise<string[]> {
  const html = await getHtml(input);
  if (!html) return [];
  const $ = cheerio.load(html);
  const found: string[] = [];
  $('link[rel="alternate"][type="application/rss+xml"], link[rel="alternate"][type="application/atom+xml"]').each((_, el) => {
    const href = $(el).attr("href");
    if (href) found.push(new URL(href, input).toString());
  });
  // YouTube channel pages embed the channelId; build the feed from it.
  const cid = html.match(/"channelId":"([\w-]+)"/);
  if (cid) found.push(`https://www.youtube.com/feeds/videos.xml?channel_id=${cid[1]}`);
  // Any anchor that looks like a feed.
  $('a[href*="rss"], a[href*="/feed"], a[href*="atom"]').each((_, el) => {
    const href = $(el).attr("href");
    if (href) found.push(new URL(href, input).toString());
  });
  return [...new Set(found)];
}

// Given any pasted URL, resolve the best way to ingest it.
export async function discoverFeed(rawInput: string): Promise<Discovered | null> {
  let input = rawInput.trim();
  if (!/^https?:\/\//i.test(input)) input = `https://${input}`;
  const base = input.replace(/\/+$/, "");

  // Tier 1: platform conventions.
  for (const c of await platformCandidates(base)) {
    const hit = await tryFeed(c);
    if (hit) return hit;
  }

  // Tier 1b: the input itself + common feed paths.
  const common = [base, `${base}/feed`, `${base}/rss`, `${base}/rss/`, `${base}/feed.xml`, `${base}/rss.xml`, `${base}/atom.xml`, `${base}/index.xml`];
  for (const c of common) {
    const hit = await tryFeed(c);
    if (hit) return hit;
  }

  // Tier 2: autodiscovery from the page.
  for (const c of await autodiscover(base)) {
    const hit = await tryFeed(c);
    if (hit) return hit;
  }

  // Tier 3: no feed anywhere — fall back to scraping the homepage for links.
  const scraped = await scrapeHomepage(base);
  if (scraped.items.length) {
    return { kind: "scrape", pollUrl: base, title: scraped.title, siteUrl: base };
  }
  return null;
}

// Lightweight feed parse (metadata + inline body only; no per-article fetch).
export async function parseFeed(feedUrl: string): Promise<Feed> {
  const feed = await parser.parseURL(feedUrl);
  const items: FeedItem[] = feed.items
    .filter((e) => e.link)
    .map((e) => ({
      guid: e.guid || (e as any).id || e.link!,
      title: (e.title || "Untitled").trim(),
      url: e.link!,
      author: (e as any).creator || (e as any).author || feed.title || null,
      publishedAt: e.isoDate || (e.pubDate ? new Date(e.pubDate).toISOString() : null),
      text: strip((e as any).contentEncoded || e.content || e.contentSnippet),
    }));
  return { title: feed.title || feedUrl, siteUrl: feed.link || null, items };
}

// ----- Scrape fallback: turn a homepage's article links into a pseudo-feed. -----
const SKIP = /\/(tag|tags|category|categories|author|about|contact|login|signup|sign-in|subscribe|privacy|terms|page\/\d+)(\/|$)/i;

export async function scrapeHomepage(pageUrl: string): Promise<Feed> {
  const html = await getHtml(pageUrl);
  if (!html) return { title: pageUrl, siteUrl: pageUrl, items: [] };
  const $ = cheerio.load(html);
  const origin = new URL(pageUrl).origin;
  const seen = new Set<string>();
  const items: FeedItem[] = [];

  // Prefer links inside article/main/post containers, then headings.
  const anchors = $("article a[href], main a[href], h1 a[href], h2 a[href], h3 a[href]");
  anchors.each((_, el) => {
    if (items.length >= 8) return;
    const href = $(el).attr("href");
    const title = $(el).text().trim();
    if (!href || title.length < 18) return; // skip nav/short labels
    let abs: string;
    try {
      abs = new URL(href, pageUrl).toString().split("#")[0];
    } catch {
      return;
    }
    if (!abs.startsWith(origin) || SKIP.test(abs) || abs.replace(/\/$/, "") === pageUrl.replace(/\/$/, "")) return;
    if (seen.has(abs)) return;
    seen.add(abs);
    items.push({ guid: abs, title, url: abs, author: null, publishedAt: null, text: "" });
  });

  const title = $("title").first().text().trim() || new URL(pageUrl).hostname;
  return { title, siteUrl: pageUrl, items };
}
