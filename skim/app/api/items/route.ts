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

// Update a story's ephemeral state: mark it seen, or save/unsave it to keep it
// past the 24h sweep. Body: { id, seen?: true, save?: boolean }.
export async function POST(req: NextRequest) {
  const { id, seen, save } = await req.json().catch(() => ({}));
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  const patch: Record<string, unknown> = {};
  if (seen) patch.seen_at = new Date().toISOString();
  if (typeof save === "boolean") patch.saved = save;
  if (Object.keys(patch).length === 0) return NextResponse.json({ error: "nothing to update" }, { status: 400 });
  const { error } = await admin().from("items").update(patch).eq("id", id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
