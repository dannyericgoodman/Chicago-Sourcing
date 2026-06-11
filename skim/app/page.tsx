import Feed from "@/components/Feed";
import { admin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

const FEED_DAYS = 7;

// One scroll of summarized posts from the last week, newest first.
async function getItems() {
  const cutoff = new Date(Date.now() - FEED_DAYS * 86400_000).toISOString();
  const { data } = await admin()
    .from("items")
    .select("id, title, url, published_at, one_liner, takeaways, key_insight, sources(title)")
    .eq("summarized", true)
    .gte("published_at", cutoff)
    .order("published_at", { ascending: false })
    .limit(200);
  return (data as any[]) || [];
}

export default async function Home() {
  const items = await getItems();

  if (!items.length) {
    return (
      <main className="feed">
        <div className="f-empty">
          <div className="big">Nothing here yet ☕️</div>
          <p>Add the newsletters and blogs you follow, then refresh.</p>
          <p><a className="navlink" href="/manage">Add sources →</a></p>
        </div>
      </main>
    );
  }

  return <Feed items={items} />;
}
