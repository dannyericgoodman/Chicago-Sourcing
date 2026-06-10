-- ▶︎ Skim one-shot setup. Paste this whole block into the Supabase SQL Editor
--   and click Run. It is safe to run more than once.

create extension if not exists "pgcrypto";

create table if not exists sources (
  id              uuid primary key default gen_random_uuid(),
  title           text not null,
  feed_url        text not null unique,   -- URL we poll (feed for rss, page for scrape)
  site_url        text,
  kind            text not null default 'rss',  -- 'rss' or 'scrape'
  muted           boolean not null default false,
  added_at        timestamptz not null default now(),
  last_checked_at timestamptz
);

create table if not exists items (
  id           uuid primary key default gen_random_uuid(),
  source_id    uuid not null references sources(id) on delete cascade,
  guid         text not null,
  title        text not null,
  url          text not null,
  author       text,
  published_at timestamptz,
  one_liner    text,
  takeaways    jsonb,
  key_insight  text,
  summarized   boolean not null default false,
  seen_at      timestamptz,
  saved        boolean not null default false,
  created_at   timestamptz not null default now(),
  unique (source_id, guid)
);

create index if not exists items_recent_idx on items (coalesce(published_at, created_at) desc);
create index if not exists items_unsummarized_idx on items (summarized) where summarized = false;
create index if not exists items_saved_idx on items (saved) where saved = true;

-- Optional: a few starter sources so the app isn't empty. Delete any you don't want.
insert into sources (title, feed_url, site_url) values
  ('Andrew Chen',        'https://andrewchen.com/feed/',          'https://andrewchen.com'),
  ('Lenny''s Newsletter','https://www.lennysnewsletter.com/feed', 'https://www.lennysnewsletter.com'),
  ('Not Boring',         'https://www.notboring.co/feed',         'https://www.notboring.co')
on conflict (feed_url) do nothing;
