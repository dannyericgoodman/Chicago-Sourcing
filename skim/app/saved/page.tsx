import { admin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

// Saved stories live here permanently — the escape hatch from the 24h sweep.
async function getSaved() {
  const { data } = await admin()
    .from("items")
    .select("id, title, url, one_liner, key_insight, published_at, sources(title)")
    .eq("saved", true)
    .order("published_at", { ascending: false })
    .limit(200);
  return (data as any[]) || [];
}

export default async function Saved() {
  const items = await getSaved();
  return (
    <main className="wrap">
      <a className="navlink" href="/">← Stories</a>
      <h1 className="h1">Saved</h1>
      <p className="sub">Stories you rescued from the 24-hour sweep.</p>

      {!items.length && <p className="sub">Nothing saved yet. Tap ☆ on a story to keep it here.</p>}

      {items.map((it) => (
        <a className="src" key={it.id} href={it.url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
          <div className="meta">
            <div className="name">{it.title}</div>
            <div className="url">{it.sources?.title || ""}{it.one_liner ? ` · ${it.one_liner}` : ""}</div>
          </div>
          <span style={{ color: "var(--muted)" }}>↗</span>
        </a>
      ))}
    </main>
  );
}
