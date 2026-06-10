-- Skim data model. Run once in the Supabase SQL editor.
-- Single-user MVP: writes happen only from server routes using the service-role key,
-- so RLS is left disabled here. Turn it on + add policies before opening to other users.

create extension if not exists "pgcrypto";

-- A blog / newsletter you follow, identified by its RSS/Atom feed.
create table if not exists sources (
  id             uuid primary key default gen_random_uuid(),
  title          text not null,
  feed_url       text not null unique,
  site_url       text,
  muted          boolean not null default false,
  added_at       timestamptz not null default now(),
  last_checked_at timestamptz
);

-- One post from a source. Summary fields are filled in after Claude runs.
create table if not exists items (
  id           uuid primary key default gen_random_uuid(),
  source_id    uuid not null references sources(id) on delete cascade,
  guid         text not null,                 -- feed entry id/guid (stable per post)
  title        text not null,
  url          text not null,
  author       text,
  published_at timestamptz,
  -- Claude output:
  one_liner    text,
  takeaways    jsonb,                          -- string[]
  key_insight  text,
  summarized   boolean not null default false,
  -- ephemeral read state (per the 24h "story" window):
  seen_at      timestamptz,
  created_at   timestamptz not null default now(),
  unique (source_id, guid)
);

-- The stories feed query hits these constantly.
create index if not exists items_recent_idx
  on items (coalesce(published_at, created_at) desc);
create index if not exists items_unsummarized_idx
  on items (summarized) where summarized = false;
