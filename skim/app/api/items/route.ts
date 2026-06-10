import { NextRequest, NextResponse } from "next/server";
import { admin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

// The stories feed: summarized posts from the last 24h, newest first.
export async function GET() {
  const cutoff = new Date(Date.now() - 24 * 3600_000).toISOString();
  const { data, error } = await admin()
    .from("items")
    .select("id, title, url, author, published_at, one_liner, takeaways, key_insight, seen_at, source_id, sources(title)")
    .eq("summarized", true)
    .gte("published_at", cutoff)
    .order("published_at", { ascending: false })
    .limit(60);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ items: data });
}

// Mark a story seen (so it visually settles / can fall away).
export async function POST(req: NextRequest) {
  const { id } = await req.json().catch(() => ({}));
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  await admin().from("items").update({ seen_at: new Date().toISOString() }).eq("id", id);
  return NextResponse.json({ ok: true });
}
