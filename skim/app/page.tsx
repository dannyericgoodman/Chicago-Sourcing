import Stories from "@/components/Stories";
import { admin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

// Server-render the last-24h stories feed straight from the DB.
async function getItems() {
  const cutoff = new Date(Date.now() - 24 * 3600_000).toISOString();
  const { data } = await admin()
    .from("items")
    .select("id, title, url, author, published_at, one_liner, takeaways, key_insight, sources(title)")
    .eq("summarized", true)
    .gte("published_at", cutoff)
    .order("published_at", { ascending: false })
    .limit(60);
  return (data as any[]) || [];
}

export default async function Home() {
  const items = await getItems();

  if (!items.length) {
    return (
      <main className="center">
        <div>
          <p style={{ fontSize: 20, color: "var(--ink)", fontWeight: 700 }}>You're all caught up ☕️</p>
          <p>No new stories in the last 24 hours.</p>
          <p><a className="navlink" href="/manage">Add newsletters & blogs →</a></p>
        </div>
      </main>
    );
  }

  return <Stories items={items} />;
}
