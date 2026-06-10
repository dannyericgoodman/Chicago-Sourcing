import { admin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

// A plain-English "is everything wired up?" screen. No secrets shown — only
// whether each piece is connected — so a non-technical setup can be verified at
// a glance. Visit /setup after deploying.

type Check = { label: string; ok: boolean; detail: string };

async function runChecks(): Promise<Check[]> {
  const checks: Check[] = [];
  const has = (k: string) => !!process.env[k]?.trim();

  checks.push({
    label: "Claude (summaries)",
    ok: has("ANTHROPIC_API_KEY"),
    detail: has("ANTHROPIC_API_KEY") ? "API key is set" : "Add ANTHROPIC_API_KEY in Vercel",
  });
  checks.push({
    label: "Daily 9am email",
    ok: has("RESEND_API_KEY"),
    detail: has("RESEND_API_KEY") ? "Resend key is set" : "Add RESEND_API_KEY in Vercel",
  });
  checks.push({
    label: "Add/remove protection",
    ok: has("APP_TOKEN") && has("NEXT_PUBLIC_APP_TOKEN"),
    detail: has("APP_TOKEN") ? "Sign-in token is set" : "Add APP_TOKEN + NEXT_PUBLIC_APP_TOKEN",
  });

  // Database: try a real query so we know the credentials actually work.
  let dbOk = false;
  let sources = 0;
  let inWindow = 0;
  let saved = 0;
  let dbDetail = "Add Supabase keys, then run the setup SQL";
  try {
    const db = admin();
    const cutoff = new Date(Date.now() - 24 * 3600_000).toISOString();
    const s = await db.from("sources").select("id", { count: "exact", head: true });
    if (s.error) throw new Error(s.error.message);
    dbOk = true;
    sources = s.count || 0;
    const w = await db.from("items").select("id", { count: "exact", head: true }).eq("summarized", true).gte("published_at", cutoff);
    inWindow = w.count || 0;
    const sv = await db.from("items").select("id", { count: "exact", head: true }).eq("saved", true);
    saved = sv.count || 0;
    dbDetail = `Connected · ${sources} sources, ${inWindow} stories live now, ${saved} saved`;
  } catch (e) {
    dbDetail = `Not connected yet — ${(e as Error).message.slice(0, 80)}`;
  }
  checks.push({ label: "Database (Supabase)", ok: dbOk, detail: dbDetail });

  return checks;
}

export default async function Setup() {
  const checks = await runChecks();
  const allGood = checks.every((c) => c.ok);

  return (
    <main className="wrap">
      <a className="navlink" href="/">← Stories</a>
      <h1 className="h1">Setup check</h1>
      <p className="sub">
        {allGood ? "Everything's connected. You're live ✅" : "Here's what's connected and what still needs a value."}
      </p>

      {checks.map((c) => (
        <div className="src" key={c.label}>
          <div style={{ fontSize: 22, width: 26 }}>{c.ok ? "✅" : "⬜️"}</div>
          <div className="meta">
            <div className="name">{c.label}</div>
            <div className="url" style={{ whiteSpace: "normal" }}>{c.detail}</div>
          </div>
        </div>
      ))}

      <p className="sub" style={{ marginTop: 20 }}>
        Once all four are green: open <a className="navlink" href="/manage" style={{ display: "inline" }}>Manage</a> to add
        newsletters, then check back at <a className="navlink" href="/" style={{ display: "inline" }}>Stories</a> tomorrow
        morning (or run a refresh).
      </p>
    </main>
  );
}
