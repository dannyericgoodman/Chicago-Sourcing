import { NextRequest, NextResponse } from "next/server";
import { admin } from "@/lib/supabase";
import { discoverFeed } from "@/lib/rss";

export const dynamic = "force-dynamic";

function authed(req: NextRequest): boolean {
  return !!process.env.APP_TOKEN && req.headers.get("x-skim-token") === process.env.APP_TOKEN;
}

export async function GET() {
  const { data, error } = await admin().from("sources").select("*").order("added_at", { ascending: false });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ sources: data });
}

// Add a source from a pasted blog/Substack/newsletter URL (or a direct feed URL).
export async function POST(req: NextRequest) {
  if (!authed(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  const { url } = await req.json().catch(() => ({}));
  if (!url) return NextResponse.json({ error: "url required" }, { status: 400 });

  const found = await discoverFeed(url);
  if (!found) return NextResponse.json({ error: "Couldn't find an RSS feed at that URL." }, { status: 422 });

  const { data, error } = await admin()
    .from("sources")
    .upsert({ title: found.title, feed_url: found.feedUrl, site_url: found.siteUrl }, { onConflict: "feed_url" })
    .select()
    .single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ source: data });
}

// Remove or mute/unmute a source.
export async function PATCH(req: NextRequest) {
  if (!authed(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  const { id, muted } = await req.json().catch(() => ({}));
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  const { error } = await admin().from("sources").update({ muted: !!muted }).eq("id", id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  if (!authed(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  const { id } = await req.json().catch(() => ({}));
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  const { error } = await admin().from("sources").delete().eq("id", id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
