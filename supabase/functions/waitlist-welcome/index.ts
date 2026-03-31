import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const FROM_EMAIL = Deno.env.get("FROM_EMAIL") ?? "Ittera <hello@ittera.ai>";
const TOTAL_SEATS = 100;

interface WaitlistRecord {
  id: string;
  email: string;
  name: string | null;
  profession: string | null;
  created_at: string;
}

interface WebhookPayload {
  type: "INSERT";
  table: string;
  record: WaitlistRecord;
  schema: string;
}

async function getPosition(supabase: ReturnType<typeof createClient>, createdAt: string): Promise<number> {
  const { count } = await supabase
    .from("waitlist")
    .select("*", { count: "exact", head: true })
    .lte("created_at", createdAt);
  return count ?? 1;
}

function firstName(name: string | null): string {
  if (!name) return "there";
  return name.trim().split(/\s+/)[0];
}

function buildEmail(record: WaitlistRecord, position: number): string {
  const name = firstName(record.name);
  const remaining = Math.max(TOTAL_SEATS - position, 0);
  const isInside = position <= TOTAL_SEATS;

  const positionBadge = isInside
    ? `<div style="display:inline-block;background:#0F172A;color:white;font-size:13px;font-weight:700;letter-spacing:-0.02em;padding:6px 14px;border-radius:8px;margin-bottom:24px;">#${position} on the list</div>`
    : `<div style="display:inline-block;background:#F5F5F4;color:#525252;font-size:13px;font-weight:600;padding:6px 14px;border-radius:8px;margin-bottom:24px;">Position #${position}</div>`;

  const bodyMessage = isInside
    ? `You're inside the first ${TOTAL_SEATS}. That means you're in the beta cohort — early access in Q2 2026, input on what we build, and early pricing locked in.<br><br>We'll reach out directly when it's time. No marketing blasts, no fluff.`
    : `You're on the list. There are ${position - TOTAL_SEATS} people ahead of you for the initial beta, but we're growing the cohort and you'll hear from us when your spot opens up.<br><br>We'll keep you posted. No noise.`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>You're on the Ittera waitlist</title>
</head>
<body style="margin:0;padding:0;background:#F9F8F6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F9F8F6;padding:40px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;">

          <!-- Header -->
          <tr>
            <td style="padding-bottom:32px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding-right:8px;vertical-align:middle;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L14.5 9L21 12L14.5 15L12 22L9.5 15L3 12L9.5 9L12 2Z" fill="#0F172A"/>
                    </svg>
                  </td>
                  <td style="font-size:15px;font-weight:700;color:#0F172A;letter-spacing:-0.02em;vertical-align:middle;">
                    Ittera
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Card -->
          <tr>
            <td style="background:white;border:1px solid #E5E5E5;border-radius:16px;padding:40px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">

              <p style="font-size:22px;font-weight:700;color:#0F172A;letter-spacing:-0.03em;margin:0 0 6px;">
                Hey ${name}, you're in.
              </p>
              <p style="font-size:14px;color:#737373;margin:0 0 28px;line-height:1.6;">
                You've joined the Ittera waitlist.
              </p>

              ${positionBadge}

              <p style="font-size:14px;color:#404040;line-height:1.75;margin:0 0 28px;">
                ${bodyMessage}
              </p>

              <!-- Divider -->
              <div style="height:1px;background:#F0F0F0;margin:0 0 28px;"></div>

              <!-- What is Ittera -->
              <p style="font-size:12px;font-weight:600;color:#A38A70;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 12px;">
                What you signed up for
              </p>
              <table cellpadding="0" cellspacing="0" width="100%">
                ${[
                  ["Smart Content Calendar", "AI-planned posting schedule built around your niche"],
                  ["Engagement Coach", "Post analysis — hook, tone, CTA, platform fit"],
                  ["Content Repurposing", "One idea expanded to LinkedIn, Twitter, Instagram, more"],
                  ["Trend Radar", "Early signals from Reddit, YouTube, Google Trends"],
                ]
                  .map(
                    ([title, desc]) => `
                <tr>
                  <td style="padding:8px 0;border-bottom:1px solid #F5F5F4;">
                    <p style="font-size:13px;font-weight:600;color:#171717;margin:0 0 2px;">${title}</p>
                    <p style="font-size:12px;color:#737373;margin:0;">${desc}</p>
                  </td>
                </tr>`,
                  )
                  .join("")}
              </table>

              <div style="height:1px;background:#F0F0F0;margin:28px 0;"></div>

              <!-- Stats strip -->
              <table cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="text-align:center;padding:0 8px;">
                    <p style="font-size:20px;font-weight:700;color:#0F172A;margin:0;">${position}</p>
                    <p style="font-size:11px;color:#A3A3A3;margin:4px 0 0;text-transform:uppercase;letter-spacing:0.06em;">Your position</p>
                  </td>
                  <td style="width:1px;background:#F0F0F0;"></td>
                  <td style="text-align:center;padding:0 8px;">
                    <p style="font-size:20px;font-weight:700;color:#0F172A;margin:0;">${remaining}</p>
                    <p style="font-size:11px;color:#A3A3A3;margin:4px 0 0;text-transform:uppercase;letter-spacing:0.06em;">Seats left</p>
                  </td>
                  <td style="width:1px;background:#F0F0F0;"></td>
                  <td style="text-align:center;padding:0 8px;">
                    <p style="font-size:20px;font-weight:700;color:#0F172A;margin:0;">Q2 '26</p>
                    <p style="font-size:11px;color:#A3A3A3;margin:4px 0 0;text-transform:uppercase;letter-spacing:0.06em;">Beta launch</p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 0 0;text-align:center;">
              <p style="font-size:11.5px;color:#A3A3A3;margin:0;line-height:1.7;">
                You're receiving this because you signed up at ittera.ai.<br/>
                No spam. You can reply directly to this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

Deno.serve(async (req) => {
  try {
    const payload: WebhookPayload = await req.json();

    // Only handle inserts into the waitlist table
    if (payload.type !== "INSERT" || payload.table !== "waitlist") {
      return new Response("ignored", { status: 200 });
    }

    const record = payload.record;

    // Get their position using the service role (bypasses RLS)
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const position = await getPosition(supabase, record.created_at);

    const html = buildEmail(record, position);

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: FROM_EMAIL,
        to: record.email,
        subject: `You're #${position} on the Ittera waitlist`,
        html,
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      console.error("Resend error:", err);
      return new Response("email failed", { status: 500 });
    }

    return new Response("ok", { status: 200 });
  } catch (err) {
    console.error("Edge function error:", err);
    return new Response("internal error", { status: 500 });
  }
});
