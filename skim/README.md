# 📲 Skim — newsletters & blogs, as stories

> "Newsletters should exist in your inbox like an Instagram story. Open & read
> within 24h → amazing. If you don't, it's gone." — Will McKelvey

Skim turns the blogs and newsletters you follow into **swipeable, ephemeral
stories**: each new post becomes a cover (title + one-liner) and an insight frame
(Claude-written takeaways + the one thing worth remembering), with a persistent
**"Read the full post ↗"** button. Posts live for **24 hours**, then fall away.

- **RSS-first ingestion** — works with Substack, beehiiv, Ghost, Medium, and most
  blogs out of the box. Paste a URL on `/manage`; Skim auto-discovers the feed.
- **Summaries by Claude** — same prompt/shape as the `vc_reading` email engine,
  generalized to any post.
- **One deploy** — Next.js on Vercel; Vercel Cron ingests every 30 min; Supabase
  stores sources + items.

## Architecture

```
Vercel Cron ─▶ GET /api/ingest ─▶ lib/ingest
                                    ├─ lib/rss.parseFeed     (pull new posts < 24h old)
                                    ├─ store in Supabase `items`
                                    └─ lib/summarize (Claude) ─▶ takeaways + insight
Browser ─▶ / (server-rendered) ─▶ components/Stories  (swipe, progress bars, 24h window)
        ─▶ /manage ─▶ /api/sources (add by URL, remove, mute)
```

Files: `lib/` engine · `app/api/` routes · `app/` + `components/Stories.tsx` UI ·
`supabase/schema.sql` data model.

## Deploy (≈15 min)

1. **Supabase** → new project → SQL editor → run `supabase/schema.sql`
   (optionally `scripts/seed-sources.sql`). Copy the project URL + **service-role** key.
2. **Anthropic** → an API key (`ANTHROPIC_API_KEY`).
3. **Vercel** → "New Project" → import this repo, set **Root Directory = `skim`**.
   Add env vars from `.env.example`:
   - `ANTHROPIC_API_KEY`, `SKIM_MODEL` (optional)
   - `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
   - `CRON_SECRET`, `APP_TOKEN`, `NEXT_PUBLIC_APP_TOKEN`
4. Deploy. `vercel.json` registers the every-30-min cron on `/api/ingest`
   (Vercel sends `Authorization: Bearer $CRON_SECRET` automatically).
5. Open the app → **/manage** → add a few newsletters → hit ingest once to seed:
   `curl -H "x-skim-token: $APP_TOKEN" https://<your-app>.vercel.app/api/ingest`

### Local dev

```bash
cd skim
npm install
cp .env.example .env.local   # fill in real values
npm run ingest:local         # one ingest pass against your Supabase
npm run dev                  # http://localhost:3000
```

## Roadmap

- **P3 — email-only newsletters:** Cloudflare Email Routing → webhook → `items`,
  for senders without RSS.
- **P3 — morning push:** Web Push "your stories are ready" at 8am.
- **Multi-user:** swap the shared `APP_TOKEN` for Supabase Auth + RLS policies.

## Notes / security

- The browser writes (add/remove sources) are gated by a shared `APP_TOKEN`
  exposed as `NEXT_PUBLIC_APP_TOKEN`. That's deliberate for a **single-user** MVP;
  it is **not** real auth. Add Supabase Auth before sharing the URL.
- The service-role key is used **only** in server routes (`lib/supabase.ts`) and
  never reaches the client.
- Add PWA icons `public/icon-192.png` and `public/icon-512.png` to enable
  install-to-home-screen (referenced by `app/manifest.ts`).
