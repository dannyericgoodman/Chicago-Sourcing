import { NextRequest, NextResponse } from "next/server";
import { sendDigest } from "@/lib/digest";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

// Triggered by Vercel Cron at 9am Central (14:00 UTC). Vercel sends
// "Authorization: Bearer $CRON_SECRET"; the app token also works for manual runs.
export async function GET(req: NextRequest) {
  const secret = process.env.CRON_SECRET;
  const auth = req.headers.get("authorization");
  const token = req.headers.get("x-skim-token");
  const ok = (secret && auth === `Bearer ${secret}`) || (process.env.APP_TOKEN && token === process.env.APP_TOKEN);
  if (!ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  try {
    const result = await sendDigest();
    return NextResponse.json({ ok: true, ...result });
  } catch (e) {
    return NextResponse.json({ ok: false, error: (e as Error).message }, { status: 500 });
  }
}
