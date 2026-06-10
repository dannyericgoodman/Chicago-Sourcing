import { admin, Source } from "./supabase";
import { parseFeed, scrapeHomepage } from "./rss";
import { summarize } from "./summarize";

const WINDOW_HOURS = 24;

// One ingest pass: pull every active feed, store genuinely-new posts, then have
// Claude summarize the unsummarized ones inside the 24h story window.
export async function runIngest(): Promise<{ found: number; summarized: number; errors: string[] }> {
  const db = admin();
  const errors: string[] = [];
  let found = 0;
  let summarized = 0;

  const { data: sources, error } = await db.from("sources").select("*").eq("muted", false);
  if (error) throw new Error(`load sources: ${error.message}`);

  for (const src of (sources || []) as Source[]) {
    try {
      // "rss" parses a feed; "scrape" diffs a homepage with no feed.
      const feed = src.kind === "scrape" ? await scrapeHomepage(src.feed_url) : await parseFeed(src.feed_url);
      const cutoff = Date.now() - WINDOW_HOURS * 3600_000;
      const fresh = feed.items.filter((i) => {
        const t = i.publishedAt ? Date.parse(i.publishedAt) : Date.now();
        return t >= cutoff; // only ingest within the story window
      });

      for (const it of fresh) {
        const { error: upErr } = await db.from("items").upsert(
          {
            source_id: src.id,
            guid: it.guid,
            title: it.title,
            url: it.url,
            author: it.author,
            // Dateless items (scraped links) enter the window now and expire 24h
            // after we first saw them — duplicates are ignored so the clock holds.
            published_at: it.publishedAt ?? new Date().toISOString(),
          },
          { onConflict: "source_id,guid", ignoreDuplicates: true },
        );
        if (!upErr) found++;
      }
      await db.from("sources").update({ last_checked_at: new Date().toISOString() }).eq("id", src.id);
    } catch (e) {
      errors.push(`${src.title}: ${(e as Error).message}`);
    }
  }

  summarized = await summarizePending();
  return { found, summarized, errors };
}

// Summarize any stored-but-unsummarized items still inside the window. Kept
// separate so a feed hiccup never blocks summaries, and vice-versa.
async function summarizePending(): Promise<number> {
  const db = admin();
  const cutoff = new Date(Date.now() - WINDOW_HOURS * 3600_000).toISOString();
  const { data: pending } = await db
    .from("items")
    .select("id, title, url, source_id, published_at")
    .eq("summarized", false)
    .order("published_at", { ascending: false })
    .limit(40);

  if (!pending?.length) return 0;
  const { data: sources } = await db.from("sources").select("id, title");
  const nameById = new Map((sources || []).map((s: any) => [s.id, s.title]));

  let n = 0;
  for (const row of pending) {
    if (row.published_at && row.published_at < cutoff) continue; // outside window; let it expire
    // Re-parse the single article cheaply via its feed text is overkill here;
    // fetch the page text directly through the same path used at ingest.
    const { parseArticleText } = await import("./article");
    const text = await parseArticleText(row.url);
    const sum = await summarize(row.title, nameById.get(row.source_id) || "a newsletter", text);
    if (sum) {
      await db
        .from("items")
        .update({
          one_liner: sum.one_liner,
          takeaways: sum.takeaways,
          key_insight: sum.key_insight,
          summarized: true,
        })
        .eq("id", row.id);
      n++;
    } else {
      // Mark summarized so we don't retry forever on un-summarizable items.
      await db.from("items").update({ summarized: true }).eq("id", row.id);
    }
  }
  return n;
}
