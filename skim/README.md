# 📲 Skim — newsletters & blogs, in one scroll

> Inspired by "newsletters should exist like an Instagram story" (Will McKelvey) —
> but built around the real job: **see the key takeaways from many newsletters in
> one scroll, and jump to the full post when something grabs you.**

Skim turns every blog and newsletter you follow into a single, clean, editorial
**scroll of insight cards** — newest first, grouped by day. Each card shows the
source, the Claude-written **one-liner + takeaways + the insight**, and a
**"Read the full post →"** link. Nothing to swipe; just skim.

- **Tiered ingestion** — paste any content-home URL on `/manage`; Skim resolves it
  via (1) platform rules (Substack/Ghost/Medium/YouTube/Reddit), (2) RSS
  autodiscovery, (3) a **homepage-scrape fallback** when no feed exists at all.
- **Summaries by Claude** — same prompt/shape as the `vc_reading` email engine,
  generalized to any post (one-liner + 3 takeaways + the insight).
- **One scroll** — a rolling 7-day feed, day dividers, per-source filter chips, and
  read cards that dim so you can triage the many at a glance.
- **Daily 9am email digest** — an optional nudge so you never forget to skim.
- **One deploy** — Next.js on Vercel; Supabase stores sources + items.

> Design preview: open `preview.html` in a browser to see the look with sample data.

## Architecture

```
Cron 8:30 ─▶ GET /api/ingest ─▶ lib/ingest
                                  ├─ lib/rss  parseFeed | scrapeHomepage (posts < 7d)
                                  ├─ store in Supabase `items`
                                  └─ lib/summarize (Claude) ─▶ one-liner + takeaways + insight
Cron 9:00 ─▶ GET /api/digest ─▶ lib/digest ─▶ Resend email "your stories are ready"
Browser ─▶ / (SSR) ─▶ components/Feed  (one scroll, day dividers, source filter, read-dimming)
        ─▶ /manage ─▶ /api/sources  (add by URL → discoverFeed, remove, mute, ↻ refresh)
        ─▶ /setup  ─▶ plain-English "is it wired up?" checks
```

Files: `lib/` engine · `app/api/` routes · `app/` + `components/Feed.tsx` UI ·
`supabase/schema.sql` + `supabase/migrations/` data model.

> **Cron frequency:** Vercel's Hobby tier runs cron **once daily per job**, which
> fits the daily-ritual model (ingest 8:30am, digest 9:00am CT / 13:30 + 14:00
> UTC). Want near-real-time ingest? Hit `/api/ingest` from an external pinger
> (GitHub Actions / cron-job.org) with the `x-skim-token` header, or use Vercel Pro.

## Deploy (≈15 min)

1. **Supabase** → new project → SQL editor → paste & run `supabase/setup.sql`
   (one block: tables + indexes + a few starter sources). Copy the project URL +
   **service-role** key.
2. **Anthropic** → an API key (`ANTHROPIC_API_KEY`). **Resend** → an API key for the
   daily digest (`RESEND_API_KEY`).
3. **Vercel** → "New Project" → import this repo, set **Root Directory = `skim`**.
   Add env vars from `.env.example`:
   - `ANTHROPIC_API_KEY`, `SKIM_MODEL` (optional)
   - `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
   - `RESEND_API_KEY`, `RESEND_FROM` (optional), `DIGEST_TO`, `APP_URL`
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
  for senders without RSS or a scrapeable homepage.
- **Web Push upgrade:** the 9am email is the reliable default; add Web Push for
  installed-PWA users who want a phone notification too.
- **Multi-user:** swap the shared `APP_TOKEN` for Supabase Auth + RLS policies.

## Notes / security

- The browser writes (add/remove sources) are gated by a shared `APP_TOKEN`
  exposed as `NEXT_PUBLIC_APP_TOKEN`. That's deliberate for a **single-user** MVP;
  it is **not** real auth. Add Supabase Auth before sharing the URL.
- The service-role key is used **only** in server routes (`lib/supabase.ts`) and
  never reaches the client.
- Add PWA icons `public/icon-192.png` and `public/icon-512.png` to enable
  install-to-home-screen (referenced by `app/manifest.ts`).
