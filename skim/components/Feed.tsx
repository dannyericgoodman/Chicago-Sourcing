"use client";

import { useEffect, useMemo, useState } from "react";

type Item = {
  id: string;
  title: string;
  url: string;
  published_at: string | null;
  one_liner: string | null;
  takeaways: string[] | null;
  key_insight: string | null;
  sources?: { title: string } | null;
};

const TOKEN = process.env.NEXT_PUBLIC_APP_TOKEN || "";
const READ_KEY = "skim:read";

function dayLabel(iso: string | null): string {
  if (!iso) return "Earlier";
  const d = new Date(iso);
  const today = new Date();
  const start = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diff = Math.round((start(today) - start(d)) / 86400_000);
  if (diff <= 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return d.toLocaleDateString(undefined, { weekday: "long" });
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function timeLabel(iso: string | null): string {
  if (!iso) return "";
  const mins = Math.round((Date.now() - Date.parse(iso)) / 60000);
  if (mins < 60) return `${Math.max(1, mins)}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
}

export default function Feed({ items }: { items: Item[] }) {
  const [read, setRead] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<string>("All");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    try {
      setRead(new Set(JSON.parse(localStorage.getItem(READ_KEY) || "[]")));
    } catch {
      /* ignore */
    }
  }, []);

  const markRead = (id: string) => {
    setRead((prev) => {
      const next = new Set(prev).add(id);
      localStorage.setItem(READ_KEY, JSON.stringify([...next]));
      return next;
    });
  };

  const sources = useMemo(() => {
    const s = new Set<string>();
    items.forEach((it) => it.sources?.title && s.add(it.sources.title));
    return ["All", ...[...s].sort()];
  }, [items]);

  const shown = filter === "All" ? items : items.filter((it) => it.sources?.title === filter);

  // Group by day, preserving newest-first order.
  const groups: { label: string; items: Item[] }[] = [];
  for (const it of shown) {
    const label = dayLabel(it.published_at);
    const g = groups[groups.length - 1];
    if (g && g.label === label) g.items.push(it);
    else groups.push({ label, items: [it] });
  }

  const refresh = async () => {
    setRefreshing(true);
    try {
      await fetch("/api/ingest", { headers: { "x-skim-token": TOKEN } });
      location.reload();
    } catch {
      setRefreshing(false);
    }
  };

  return (
    <>
      <header className="f-top">
        <span className="f-brand">SkimIt</span>
        <div className="f-actions">
          <button onClick={refresh} disabled={refreshing}>{refreshing ? "Refreshing…" : "↻ Refresh"}</button>
          <a href="/manage">Manage</a>
        </div>
      </header>

      {sources.length > 2 && (
        <div className="f-chips">
          {sources.map((s) => (
            <button key={s} className={`chip ${filter === s ? "on" : ""}`} onClick={() => setFilter(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <main className="feed">
        {groups.map((g) => (
          <section key={g.label}>
            <div className="f-day">{g.label}</div>
            {g.items.map((it) => (
              <article key={it.id} className={`f-post ${read.has(it.id) ? "read" : ""}`}>
                <div className="f-meta">
                  <span className="f-source">{it.sources?.title || "Newsletter"}</span>
                  <span className="f-dot">·</span>
                  <span>{timeLabel(it.published_at)}</span>
                </div>
                <a className="f-title" href={it.url} target="_blank" rel="noreferrer" onClick={() => markRead(it.id)}>
                  {it.title}
                </a>
                {it.one_liner && <p className="f-hook">{it.one_liner}</p>}
                {it.takeaways && it.takeaways.length > 0 && (
                  <ul className="f-tk">{it.takeaways.map((t, k) => <li key={k}>{t}</li>)}</ul>
                )}
                {it.key_insight && (
                  <p className="f-insight"><b>The insight — </b>{it.key_insight}</p>
                )}
                <a className="f-more" href={it.url} target="_blank" rel="noreferrer" onClick={() => markRead(it.id)}>
                  Read the full post →
                </a>
              </article>
            ))}
          </section>
        ))}
      </main>
    </>
  );
}
