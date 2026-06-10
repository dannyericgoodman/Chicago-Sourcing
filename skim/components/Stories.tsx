"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type Item = {
  id: string;
  title: string;
  url: string;
  author: string | null;
  published_at: string | null;
  one_liner: string | null;
  takeaways: string[] | null;
  key_insight: string | null;
  sources?: { title: string } | null;
};

// Each post becomes two frames: a cover, then the takeaways/insight.
type Frame = { item: Item; kind: "cover" | "insight" };

function expiresIn(iso: string | null): string {
  if (!iso) return "";
  const ms = Date.parse(iso) + 24 * 3600_000 - Date.now();
  if (ms <= 0) return "expiring";
  const h = Math.floor(ms / 3600_000);
  const m = Math.floor((ms % 3600_000) / 60_000);
  return h >= 1 ? `${h}h left` : `${m}m left`;
}

export default function Stories({ items }: { items: Item[] }) {
  const frames: Frame[] = useMemo(
    () => items.flatMap((item) => [{ item, kind: "cover" as const }, { item, kind: "insight" as const }]),
    [items],
  );
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const frame = frames[i];

  const toggleSave = useCallback((id: string) => {
    setSaved((s) => {
      const next = !s[id];
      fetch("/api/items", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ id, save: next }),
      }).catch(() => {});
      return { ...s, [id]: next };
    });
  }, []);

  const next = useCallback(() => setI((v) => Math.min(v + 1, frames.length - 1)), [frames.length]);
  const prev = useCallback(() => setI((v) => Math.max(v - 1, 0)), []);

  // Mark the post seen once we reach its insight frame.
  useEffect(() => {
    if (frame?.kind === "insight") {
      fetch("/api/items", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ id: frame.item.id }),
      }).catch(() => {});
    }
  }, [frame]);

  // Auto-advance timer, IG-style. Pause on hold.
  useEffect(() => {
    if (paused || !frame) return;
    const dur = frame.kind === "cover" ? 5000 : 9000;
    const t = setTimeout(next, dur);
    return () => clearTimeout(t);
  }, [i, paused, frame, next]);

  // Keyboard for desktop testing.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  if (!frame) return null;
  const it = frame.item;
  const source = it.sources?.title || it.author || "Newsletter";

  return (
    <div className="stage">
      <div className="bars">
        {frames.map((_, idx) => (
          <div key={idx} className={`bar ${idx < i ? "done" : ""} ${idx === i && !paused ? "active" : ""}`} style={{ "--dur": frame.kind === "cover" ? "5s" : "9s" } as React.CSSProperties}>
            <i />
          </div>
        ))}
      </div>

      <div className="topbar">
        <span>{source}</span>
        <span style={{ display: "flex", gap: 14, alignItems: "center" }}>
          <span>{expiresIn(it.published_at)}</span>
          <button
            onClick={() => toggleSave(it.id)}
            aria-label={saved[it.id] ? "Saved" : "Save"}
            style={{ background: "none", border: "none", color: saved[it.id] ? "#ffd24a" : "var(--muted)", fontSize: 20, cursor: "pointer", padding: 0, lineHeight: 1 }}
          >
            {saved[it.id] ? "★" : "☆"}
          </button>
          <a href="/saved">saved</a>
        </span>
      </div>

      <div
        className="card"
        onPointerDown={() => setPaused(true)}
        onPointerUp={() => setPaused(false)}
        onPointerLeave={() => setPaused(false)}
      >
        {frame.kind === "cover" ? (
          <>
            <div className="eyebrow">{source}</div>
            <h1 className="title">{it.title}</h1>
            {it.one_liner && <p className="oneliner">{it.one_liner}</p>}
          </>
        ) : (
          <>
            <p className="label">Takeaways</p>
            <ul className="takeaways">{(it.takeaways || []).map((t, k) => <li key={k}>{t}</li>)}</ul>
            {it.key_insight && <div className="insight"><strong>Worth remembering — </strong>{it.key_insight}</div>}
          </>
        )}

        <div className="zones">
          <div className="prev" onClick={prev} />
          <div className="next" onClick={next} />
        </div>
      </div>

      <div className="cta">
        <a href={it.url} target="_blank" rel="noreferrer">Read the full post ↗</a>
      </div>
    </div>
  );
}
