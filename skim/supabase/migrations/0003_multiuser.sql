-- Phase 2 — multi-user foundation. ADDITIVE ONLY: this adds new tables and does
-- not touch `sources` or `items`, so the deployed single-user app keeps working
-- (it uses the service-role key, which bypasses RLS). Apply this when we start
-- wiring accounts; the app refactor (Supabase Auth + reading per-user state) lands
-- alongside it.
--
-- Model in one line: newsletters (`sources`) and their Claude summaries (`items`)
-- stay GLOBAL and shared — ingested once, fanned out — while who-follows-what,
-- read state, and saved quotes/notes are PER-USER below.

-- Public-ish profile, one per auth user. Handle powers "follow Danny's list".
create table if not exists profiles (
  id           uuid primary key references auth.users on delete cascade,
  handle       text unique not null,
  display_name text,
  avatar_url   text,
  bio          text,
  created_at   timestamptz not null default now()
);

-- Which newsletters a person follows (+ per-user mute, replacing the global one).
create table if not exists follows (
  user_id    uuid not null references auth.users on delete cascade,
  source_id  uuid not null references sources(id) on delete cascade,
  muted      boolean not null default false,
  created_at timestamptz not null default now(),
  primary key (user_id, source_id)
);

-- Follow a *person* to absorb their reading list (the social-curation magic).
create table if not exists follow_people (
  follower_id uuid not null references auth.users on delete cascade,
  followee_id uuid not null references auth.users on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (follower_id, followee_id),
  check (follower_id <> followee_id)
);

-- Per-user read state (replaces items.seen_at once multi-user is live).
create table if not exists reads (
  user_id uuid not null references auth.users on delete cascade,
  item_id uuid not null references items(id) on delete cascade,
  read_at timestamptz not null default now(),
  primary key (user_id, item_id)
);

-- Second brain: a saved quote and/or note. Optional one-way sync to Notion.
create table if not exists highlights (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users on delete cascade,
  item_id     uuid references items(id) on delete set null,
  source_id   uuid references sources(id) on delete set null,
  quote       text,
  note        text,
  notion_url  text,                       -- set after a successful Notion push
  created_at  timestamptz not null default now()
);

create index if not exists follows_user_idx     on follows (user_id);
create index if not exists follow_people_f_idx   on follow_people (follower_id);
create index if not exists highlights_user_idx   on highlights (user_id, created_at desc);

-- ---- Row-level security: a person only ever touches their own rows. ----
alter table profiles      enable row level security;
alter table follows       enable row level security;
alter table follow_people enable row level security;
alter table reads         enable row level security;
alter table highlights    enable row level security;

-- Profiles are readable by any signed-in user (needed to discover/follow people),
-- but writable only by their owner.
create policy "profiles readable by authed" on profiles
  for select using (auth.role() = 'authenticated');
create policy "own profile write" on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

-- Follows / reads / highlights: fully private to the owner.
create policy "own follows" on follows
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own reads" on reads
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own highlights" on highlights
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Follow-graph: you manage rows where you are the follower; anyone signed in can
-- see who follows whom (for follower counts / "followed by"). Tighten later if needed.
create policy "manage own follow_people" on follow_people
  for all using (auth.uid() = follower_id) with check (auth.uid() = follower_id);
create policy "read follow_people" on follow_people
  for select using (auth.role() = 'authenticated');
