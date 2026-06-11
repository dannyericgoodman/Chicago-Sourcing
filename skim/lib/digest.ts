import { admin } from "./supabase";

// The daily 9am nudge: one email listing the stories waiting in the app. This is
// the safety net that lets the in-app feed stay ephemeral — open it once a day
// and you never miss anything. Reuses Resend (same backend as vc_reading).

const APP_URL = process.env.APP_URL || "https://skim.vercel.app";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function currentStories() {
  const cutoff = new Date(Date.now() - 24 * 3600_000).toISOString();
  const { data } = await admin()
    .from("items")
    .select("title, url, one_liner, sources(title)")
    .eq("summarized", true)
    .gte("published_at", cutoff)
    .order("published_at", { ascending: false })
    .limit(60);
  return (data as any[]) || [];
}

function renderHtml(items: any[]): string {
  const rows = items
    .map(
      (it) => `
      <tr><td style="padding:0 0 18px;">
        <div style="font-size:12px;letter-spacing:1px;text-transform:uppercase;color:#4a6cf7;font-weight:700;">${esc(it.sources?.title || "")}</div>
        <a href="${esc(it.url)}" style="color:#0f172a;text-decoration:none;font-size:18px;font-weight:700;line-height:1.3;">${esc(it.title)}</a>
        ${it.one_liner ? `<div style="color:#52617a;font-size:14px;margin-top:4px;">${esc(it.one_liner)}</div>` : ""}
      </td></tr>`,
    )
    .join("");
  return `<!DOCTYPE html><html><body style="margin:0;background:#eef1f6;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:28px 14px;">
      <table width="100%" style="max-width:560px;background:#fff;border-radius:14px;padding:26px;">
        <tr><td style="font-size:22px;font-weight:800;color:#0f172a;padding-bottom:4px;">Your reading is ready ☕️</td></tr>
        <tr><td style="color:#52617a;font-size:14px;padding-bottom:22px;">${items.length} new ${items.length === 1 ? "post" : "posts"} from the newsletters you follow, distilled.</td></tr>
        ${rows}
        <tr><td style="padding-top:8px;">
          <a href="${esc(APP_URL)}" style="display:inline-block;background:#4a6cf7;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:700;font-size:15px;">Open SkimIt →</a>
        </td></tr>
      </table>
    </td></tr></table></body></html>`;
}

export async function sendDigest(): Promise<{ sent: boolean; count: number; reason?: string }> {
  const items = await currentStories();
  if (!items.length) return { sent: false, count: 0, reason: "no stories" };

  const key = process.env.RESEND_API_KEY?.trim();
  if (!key) return { sent: false, count: items.length, reason: "RESEND_API_KEY not set" };

  const from = process.env.RESEND_FROM || "SkimIt <onboarding@resend.dev>";
  const to = (process.env.DIGEST_TO || process.env.NEWSLETTER_TO || "danny.eric.goodman@gmail.com")
    .split(",")
    .map((s) => s.trim());

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from,
      to,
      subject: `☕️ ${items.length} new takeaways from your newsletters`,
      html: renderHtml(items),
    }),
  });
  if (!res.ok) return { sent: false, count: items.length, reason: `Resend HTTP ${res.status}: ${(await res.text()).slice(0, 200)}` };
  return { sent: true, count: items.length };
}
