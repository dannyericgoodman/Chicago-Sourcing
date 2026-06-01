# 📚 The VC Reading Room

A daily email to help you become an elite venture investor. Every morning it
picks **one curated essay each** from **Paul Graham**, **Bill Gurley**, and
**Andrew Chen**, links to it, and includes **Claude-written key takeaways +
"investor angle"** tailored to that goal.

Runs on a GitHub Actions cron — no server. Deliberately simple:

- **Selection** is deterministic by date from hand-curated, ordered lists
  (`essays.py`) — foundations first, then sharper investor judgment. No scraping
  needed to choose; it advances one step per author per day and cycles.
- **Summaries**: `summarize.py` fetches the essay and has Claude distill it;
  if a site blocks the fetch, Claude summarizes the known essay from memory
  (with a guard against making things up).
- **Delivery**: `deliver.py` — **Resend** (recommended) or **Gmail SMTP**.
- **De-dup**: a one-line `last_sent_date` lets the workflow fire several times
  each morning (for reliability) while sending **at most one** email/day.

## Setup (one secret + done)

In **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Required | Notes |
|--------|----------|-------|
| `ANTHROPIC_API_KEY` | for summaries | already used by this repo |
| `RESEND_API_KEY` | **recommended email** | see below — most reliable |
| `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` | alt email | needs 2FA + a 16-char App Password |
| `NEWSLETTER_TO` | optional | recipient; defaults to your inbox |
| `NOTION_API_KEY` + `NOTION_DATABASE_ID` | optional | also archive each issue to Notion |

### Email via Resend (recommended — no App Password headaches)
1. Sign up free at <https://resend.com> using **danny.eric.goodman@gmail.com**.
2. **API Keys → Create API Key** → copy it (`re_...`).
3. Add it as the `RESEND_API_KEY` secret.

That's it. With the default `onboarding@resend.dev` sender you can email your own
signup address with **no domain setup**. (To send from a custom address, verify a
domain in Resend and set a `RESEND_FROM` Actions *variable*.)

## Run it
- **Automatic:** four attempts each morning (`~7:13–8:41am Central`); de-dup
  ensures one email. Retime via the `cron:` lines (UTC) in
  `.github/workflows/daily-reading.yml`.
- **Manual / test:** Actions → *Daily VC Reading Newsletter* → **Run workflow**
  (forces a send immediately).
- **Local:** `python -m vc_reading.newsletter --dry-run` (writes `data/preview.html`).

## Troubleshooting
Every run logs a **Preflight** line showing which backends are set, and **exits
red** if the email fails (so GitHub notifies you) — open the *Send newsletter*
step to see the exact reason. A failed send does **not** mark the day done, so the
next attempt retries. If a green run still yields no email, check Spam/Promotions.
