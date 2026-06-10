-- Optional starter pack. Run in the Supabase SQL editor to pre-load a few feeds,
-- or just add them from the /manage screen. (These are public RSS feeds.)
insert into sources (title, feed_url, site_url) values
  ('Stratechery (free)', 'https://stratechery.com/feed/', 'https://stratechery.com'),
  ('Andrew Chen',        'https://andrewchen.com/feed/',  'https://andrewchen.com'),
  ('Paul Graham (essays)','http://www.aaronsw.com/2002/feeds/pgessays.rss', 'https://paulgraham.com'),
  ('Lenny''s Newsletter','https://www.lennysnewsletter.com/feed', 'https://www.lennysnewsletter.com'),
  ('Not Boring',         'https://www.notboring.co/feed', 'https://www.notboring.co')
on conflict (feed_url) do nothing;
