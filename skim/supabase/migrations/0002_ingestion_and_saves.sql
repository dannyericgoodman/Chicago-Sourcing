-- Migration: multi-method ingestion + save-to-keep. Run after schema.sql.

-- How a source is polled: 'rss' (a feed) or 'scrape' (diff a homepage's links).
alter table sources add column if not exists kind text not null default 'rss';

-- Rescue a story from the 24h sweep into a permanent /saved list.
alter table items add column if not exists saved boolean not null default false;

create index if not exists items_saved_idx on items (saved) where saved = true;
