import { createClient } from "@supabase/supabase-js";

// Server-only client. Uses the service-role key, so it must never be imported
// into a "use client" component or shipped to the browser.
export function admin() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
  }
  return createClient(url, key, { auth: { persistSession: false } });
}

export type Source = {
  id: string;
  title: string;
  feed_url: string;
  site_url: string | null;
  muted: boolean;
  added_at: string;
  last_checked_at: string | null;
};

export type Item = {
  id: string;
  source_id: string;
  guid: string;
  title: string;
  url: string;
  author: string | null;
  published_at: string | null;
  one_liner: string | null;
  takeaways: string[] | null;
  key_insight: string | null;
  summarized: boolean;
  seen_at: string | null;
  created_at: string;
};
