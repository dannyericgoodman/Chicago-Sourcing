# Skim — product roadmap

**The spine:** *Follow great readers, not just newsletters — and let what you read
compound into a second brain.* The daily digest is the surface; the magic is
social curation + capture.

## Decisions (locked)

| Question | Decision |
|---|---|
| How friends' feeds combine | **Follow people & their lists** — profiles with reading lists; follow a person to absorb their newsletters, or cherry-pick from a shared catalog |
| Audience | **Invite-only & private** to start — not a public social network; lists private unless shared |
| Capture / second brain | **In-app highlights + notes**, with **optional one-way Notion sync** |
| Sequencing | **Deploy the personal digest now**; layer accounts → social → capture on top without losing the live site or data |

## Architecture principle

Newsletters (`sources`) and their Claude summaries (`items`) are **global and
shared** — ingested and summarized **once**, fanned out to everyone who follows
them. Everything personal — who-follows-what, read state, saved quotes/notes — is
**per-user** (see `supabase/migrations/0003_multiuser.sql`). Net effect:
**summarization cost scales with the number of newsletters, not the number of
users.** Fifty friends following Stratechery = one summary.

## Phases

- **P1 — Personal digest (built; deploying).** One clean scroll of Claude
  takeaways across the newsletters you follow; tiered RSS/scrape ingestion; daily
  9am email; `/manage`, `/setup`. Next + Vercel + Supabase.
- **P2 — Accounts & follows.** Supabase Auth (magic-link, no passwords) + RLS.
  The feed becomes "the shared pool filtered to what *I* follow." Per-user mute &
  read state move off `items` into `follows` / `reads`. *(This is the main
  refactor — swap the single service-role data layer for per-user auth.)*
- **P3 — Social curation.** Profiles + handles; "follow Danny's reading list";
  following a person blends their sources into your feed; a catalog to discover
  what friends read. Invite-only.
- **P4 — Second brain.** Highlight a takeaway or quote and jot a note on any post
  (`highlights`); a personal library view; **optional one-way Notion sync** (push
  saved quotes/notes to a Notion database for those who connect it).

## Open / later

- **Cost guardrails** if it grows beyond friends (per-user source caps, or
  bring-your-own Anthropic key).
- **Email-only newsletters** (no RSS): per-user forwarding address via Cloudflare
  Email Routing → webhook. Heavier with multi-user; deferred.
- **Own repo:** Skim should live in its own GitHub repo (separate product). Blocked
  today because this work session is scoped to existing repos; do this as a tidy-up.
