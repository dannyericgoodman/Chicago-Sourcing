import { NextRequest, NextResponse } from "next/server";
import { runIngest } from "@/lib/ingest";

export const dynamic = "force-dynamic";
export const maxDuration = 300; // allow longer summarize batches

// Triggered by Vercel Cron (every 30 min) and by the "refresh" button.
// Vercel Cron sends "Authorization: Bearer $CRON_SECRET".
export async function GET(req: NextRequest) {
  const secret = process.env.CRON_SECRET;
  const auth = req.headers.get("authorization");
  const token = req.headers.get("x-skim-token");
  const ok = (secret && auth === `Bearer ${secret}`) || (process.env.APP_TOKEN && token === process.env.APP_TOKEN);
  if (!ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  try {
    const result = await runIngest();
    return NextResponse.json({ ok: true, ...result });
  } catch (e) {
    return NextResponse.json({ ok: false, error: (e as Error).message }, { status: 500 });
  }
}
