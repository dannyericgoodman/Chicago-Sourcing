# 📚 The VC Reading Room

A daily newsletter to help you study the canon of early-stage venture capital.
Every morning it picks **one classic essay each** from **Paul Graham**, **Bill
Gurley**, and **Andrew Chen**, has **Claude (Opus 4.8)** distill 3–5 key
takeaways + an "investor angle" for each, and delivers it two ways:

- **📧 Email** to your inbox (`danny.eric.goodman@gmail.com` by default), and
- **🗄️ Notion** — one archive page per day in your **VC Daily Reading** database.

It runs entirely on a **GitHub Actions cron** — no server, no laptop, nothing to
babysit. It rotates through each author's full archive without repeating, and
only recycles once you've seen everything.

---

## How it works

```
GitHub Actions (daily cron)
        │
        ├─ build candidate pool  ── Paul Graham   → scrapes paulgraham.com/articles.html
        │  (cached weekly)          Bill Gurley    → abovethecrowd.com WordPress REST API
        │                           Andrew Chen    → andrewchen.com  WordPress REST API
        │
        ├─ pick 1 unseen essay per author  (rotation tracked in data/state.json)
        ├─ fetch full text  →  Claude Opus 4.8  →  takeaways + investor angle
        ├─ render HTML + plain-text email
        ├─ send via Gmail SMTP        (deliver.send_email)
        ├─ archive to Notion          (deliver.archive_to_notion)
        └─ commit updated rotation state back to the repo
```

Everything degrades gracefully: if a source site is unreachable, it falls back
to a cached pool then to an embedded seed; if the model call fails, the essay
still goes out with a "read it directly" note. A missing credential just skips
that one channel.

### Files
| File | Purpose |
|------|---------|
| `sources.py` | Build the candidate pool & fetch full essay text |
| `summarize.py` | Claude Opus 4.8 → takeaways JSON |
| `render.py` | HTML + plain-text email rendering |
| `deliver.py` | Gmail SMTP + Notion archive |
| `newsletter.py` | Orchestrator + CLI (`python -m vc_reading.newsletter`) |
| `data/pool_cache.json` | Cached pool of essays (rebuilt weekly) |
| `data/state.json` | Which essays have already been sent (no-repeat rotation) |

---

## One-time setup (~10 minutes)

All configuration is via **GitHub repository secrets**
(`Settings → Secrets and variables → Actions → New repository secret`).

### 1. Anthropic (required for takeaways)
| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (the repo's sourcing engine already uses this) |

> Model defaults to `claude-opus-4-8`. To change it, add an Actions **variable**
> (not secret) named `VC_MODEL`, e.g. `claude-haiku-4-5-20251001` to cut cost.

### 2. Email — Gmail App Password (required for the email blast)
Gmail blocks plain passwords, so create an **App Password**:
1. Enable 2-Step Verification on your Google account.
2. Go to <https://myaccount.google.com/apppasswords>, create one named "VC Reading".
3. Add these secrets:

| Secret | Value |
|--------|-------|
| `GMAIL_ADDRESS` | The Gmail account that *sends* (e.g. `danny.eric.goodman@gmail.com`) |
| `GMAIL_APP_PASSWORD` | The 16-character app password (no spaces) |
| `NEWSLETTER_TO` | *(optional)* recipient(s), comma-separated. Defaults to `GMAIL_ADDRESS`, then to `danny.eric.goodman@gmail.com` |

### 3. Notion archive (required for the Notion copy)
A database called **"VC Daily Reading"** has already been created in your
workspace:

- **Database ID:** `f1571e20921b4e5286c93a9ab45f3245`

To let the GitHub Action write to it you need an **internal integration token**:
1. Go to <https://www.notion.so/my-integrations> → **New integration** →
   name it "VC Reading", workspace = yours → copy the **Internal Integration Secret** (`secret_…` / `ntn_…`).
2. Open the **VC Daily Reading** database in Notion → top-right `•••` →
   **Connections** → add your "VC Reading" integration (this grants it write access).
3. Add these secrets:

| Secret | Value |
|--------|-------|
| `NOTION_API_KEY` | The integration secret from step 1 |
| `NOTION_DATABASE_ID` | `f1571e20921b4e5286c93a9ab45f3245` |

> If you skip Notion, just don't set these two — the email still sends.

---

## Run it

- **Automatic:** every day at **12:00 UTC (~7am Central)** via
  `.github/workflows/daily-reading.yml`. Change the `cron:` line to retime it
  (cron is in UTC).
- **Manual / first test:** GitHub → **Actions** tab → *Daily VC Reading
  Newsletter* → **Run workflow**.
- **Locally:**
  ```bash
  pip install -r requirements.txt
  python -m vc_reading.newsletter --dry-run   # writes data/preview.html, no send
  python -m vc_reading.newsletter             # real send (needs the env vars above)
  python -m vc_reading.newsletter --refresh   # force-rebuild the essay pool
  ```

---

## Cost
Three short Opus 4.8 summaries/day ≈ a few cents/day. Switch `VC_MODEL` to a
Haiku model to make it nearly free.

## Notes
- **Rotation** is stored in `data/state.json` and committed back by the Action
  after each run, so you won't see repeats until an author's archive is
  exhausted. To reset, set `{"sent": {}}`.
- Paul Graham's site serves plain HTML; Gurley and Chen run WordPress, so the
  pool is built from their `/wp-json/wp/v2/posts` API — robust and complete.
- The pool refreshes at most weekly (`POOL_MAX_AGE_DAYS` in `newsletter.py`), so
  new posts by these authors are automatically picked up.
