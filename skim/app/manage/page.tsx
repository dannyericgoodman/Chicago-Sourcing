"use client";

import { useEffect, useState } from "react";

type Source = { id: string; title: string; feed_url: string; site_url: string | null; muted: boolean };

// Single-user MVP: the shared token is baked in as a public env so the manage
// screen can write. Swap for real auth (e.g. Supabase Auth) before multi-user.
const TOKEN = process.env.NEXT_PUBLIC_APP_TOKEN || "";

export default function Manage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");

  // Pull new posts + summarize right now, instead of waiting for the 8:30am cron.
  const refresh = async () => {
    setRefreshing(true); setErr(""); setNote("Checking your sources…");
    try {
      const r = await fetch("/api/ingest", { headers: { "x-skim-token": TOKEN } });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || "Refresh failed");
      setNote(`Done — ${j.found} new, ${j.summarized} summarized. Open Stories →`);
    } catch (e) {
      setErr((e as Error).message);
      setNote("");
    } finally {
      setRefreshing(false);
    }
  };

  const load = async () => {
    const r = await fetch("/api/sources");
    const j = await r.json();
    setSources(j.sources || []);
  };
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!url.trim()) return;
    setBusy(true); setErr("");
    try {
      const r = await fetch("/api/sources", {
        method: "POST",
        headers: { "content-type": "application/json", "x-skim-token": TOKEN },
        body: JSON.stringify({ url: url.trim() }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || "Failed to add");
      setUrl("");
      await load();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    await fetch("/api/sources", {
      method: "DELETE",
      headers: { "content-type": "application/json", "x-skim-token": TOKEN },
      body: JSON.stringify({ id }),
    });
    load();
  };

  const toggleMute = async (s: Source) => {
    await fetch("/api/sources", {
      method: "PATCH",
      headers: { "content-type": "application/json", "x-skim-token": TOKEN },
      body: JSON.stringify({ id: s.id, muted: !s.muted }),
    });
    load();
  };

  return (
    <main className="wrap">
      <a className="navlink" href="/">← Stories</a>
      <h1 className="h1">Your sources</h1>
      <p className="sub">Paste a Substack, blog, or newsletter URL — we'll find its feed.</p>

      {err && <p className="err">{err}</p>}
      {note && <p className="sub" style={{ color: "var(--accent)" }}>{note}</p>}

      <div className="addrow">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="stratechery.com  ·  example.substack.com"
          inputMode="url"
          autoCapitalize="none"
        />
        <button className="btn" onClick={add} disabled={busy}>{busy ? "…" : "Add"}</button>
      </div>

      {sources.length > 0 && (
        <button
          onClick={refresh}
          disabled={refreshing}
          style={{ width: "100%", marginBottom: 22, background: "transparent", border: "1px solid #2a3344", color: "var(--ink)", borderRadius: 10, padding: "12px", fontSize: 15, fontWeight: 600, cursor: "pointer" }}
        >
          {refreshing ? "Refreshing…" : "↻ Refresh now"}
        </button>
      )}

      {sources.map((s) => (
        <div className="src" key={s.id}>
          <div className="meta">
            <div className="name">{s.title}</div>
            <div className="url">{s.site_url || s.feed_url}</div>
          </div>
          <button onClick={() => toggleMute(s)}>{s.muted ? "Unmute" : "Mute"}</button>
          <button onClick={() => remove(s.id)}>Remove</button>
        </div>
      ))}

      {!sources.length && <p className="sub">No sources yet. Add your first above.</p>}
    </main>
  );
}
