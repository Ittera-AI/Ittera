import logging
import smtplib
from email.message import EmailMessage
from html import escape

from app.config import settings

logger = logging.getLogger(__name__)


def _mail_is_configured() -> bool:
    return all([settings.SMTP_HOST, settings.MAIL_FROM])


def _first_name(name: str | None, email: str) -> str:
    if name:
        return name.strip().split()[0]
    local = email.split("@")[0].replace(".", " ").replace("_", " ").split()
    return local[0].capitalize() if local else "there"


def _waitlist_email_copy(position: int) -> dict[str, str]:
    inside = position <= settings.WAITLIST_TOTAL_SEATS
    return {
        "subject": "You're in — Ittera beta waitlist confirmed" if inside else "You're on the Ittera waitlist",
        "eyebrow": "Waitlist confirmed",
        "headline": "You're in." if inside else "You're on the list.",
        "position": f"#{position}",
        "position_label": "Your spot" if inside else "Your position",
        "summary": (
            f"You're one of the first {settings.WAITLIST_TOTAL_SEATS} people on the Ittera waitlist. "
            "That puts you in the first group we invite when beta opens."
        ) if inside else (
            f"The first {settings.WAITLIST_TOTAL_SEATS} people get earliest beta access. "
            "We'll work through the list as capacity opens up."
        ),
        "product_line": (
            "Ittera is an AI content strategy engine — not a scheduler, not a generator. "
            "It watches your audience, maps what works, and keeps your content compounding."
        ),
    }


def send_waitlist_confirmation_email(
    email: str,
    position: int,
    name: str | None = None,
) -> None:
    if not _mail_is_configured():
        return

    first = _first_name(name, email)
    sign_in_url = settings.FRONTEND_URL.rstrip("/")
    safe_url = escape(sign_in_url, quote=True)
    c = _waitlist_email_copy(position)

    # ── plain text ──────────────────────────────────────────────────────────
    text_body = (
        f"Hey {first},\n\n"
        f"{c['headline']}\n\n"
        f"{c['summary']}\n\n"
        f"{c['product_line']}\n\n"
        f"Your spot: {c['position']}\n\n"
        "What happens next:\n"
        "1. Use this same email to create your Ittera account.\n"
        "2. We'll email you the moment your beta access opens.\n"
        "3. You'll be among the first to test the product and shape what we build.\n\n"
        "Visit: https://ittera.in\n\n"
        "— The Ittera team\n\n"
        f"---\nTo unsubscribe, reply with 'unsubscribe' or email admin.ittera@gmail.com\n"
    )

    # ── html ────────────────────────────────────────────────────────────────
    html_body = f"""<!doctype html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta name="x-apple-disable-message-reformatting"/>
  <meta name="format-detection" content="telephone=no,date=no,address=no,email=no"/>
  <title>{escape(c["subject"])}</title>
  <style>
    /* ── reset ── */
    body, table, td {{ margin:0; padding:0; }}
    img {{ border:0; display:block; max-width:100%; }}
    a {{ color:inherit; }}

    /* ── mobile ── */
    @media only screen and (max-width:600px) {{
      .outer-pad {{ padding:20px 12px 24px !important; }}
      .card {{ border-radius:20px !important; padding:28px 20px !important; }}
      .headline {{ font-size:28px !important; }}
      .summary {{ font-size:14px !important; }}
      .pos-block {{ padding:20px 18px !important; border-radius:16px !important; }}
      .pos-number {{ font-size:38px !important; }}
      .pos-body {{ font-size:12px !important; }}
      .next-block {{ padding:20px 18px !important; border-radius:16px !important; }}
      .step-text {{ font-size:13px !important; }}
      .cta-wrap {{ width:100% !important; }}
      .cta-cell {{ border-radius:14px !important; display:block !important; }}
      .cta-link {{ display:block !important; text-align:center !important; padding:15px 20px !important; font-size:15px !important; border-radius:14px !important; }}
      .signoff {{ font-size:13px !important; margin-top:22px !important; }}
      .footer-td {{ font-size:11px !important; padding:16px 4px 0 !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#F4EFE8;-webkit-font-smoothing:antialiased;mso-line-height-rule:exactly;">

<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#F4EFE8;">
<tr><td align="center" class="outer-pad" style="padding:40px 16px 32px;">

  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:560px;">

    <!-- wordmark -->
    <tr>
      <td style="padding-bottom:22px;text-align:center;">
        <span style="font-family:Georgia,'Times New Roman',serif;font-size:22px;font-weight:700;letter-spacing:-0.03em;color:#2B241E;">
          Ittera
        </span>
      </td>
    </tr>

    <!-- main card -->
    <tr>
      <td class="card" style="background:#FFFFFF;border:1px solid #E8E0D6;border-radius:28px;padding:40px 36px;word-break:break-word;">

        <!-- eyebrow -->
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#A38A70;">
          {escape(c["eyebrow"])}
        </div>

        <!-- headline -->
        <h1 class="headline" style="margin:14px 0 0;font-family:Georgia,'Times New Roman',serif;font-size:36px;line-height:1.08;font-weight:700;letter-spacing:-0.03em;color:#1A1614;">
          Hey {escape(first)},<br/>{escape(c["headline"])}
        </h1>

        <!-- summary -->
        <p class="summary" style="margin:16px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.75;color:#5F5A54;">
          {escape(c["summary"])}
        </p>

        <!-- position block -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:26px;">
          <tr>
            <td class="pos-block" style="background:#1A1614;border-radius:20px;padding:24px 26px;">
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:rgba(244,239,232,0.45);">
                {escape(c["position_label"])}
              </div>
              <div class="pos-number" style="margin-top:8px;font-family:Georgia,'Times New Roman',serif;font-size:52px;line-height:1;font-weight:700;letter-spacing:-0.05em;color:#C4A882;">
                {escape(c["position"])}
              </div>
              <p class="pos-body" style="margin:12px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.7;color:rgba(244,239,232,0.62);">
                {escape(c["product_line"])}
              </p>
            </td>
          </tr>
        </table>

        <!-- what's next -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:20px;">
          <tr>
            <td class="next-block" style="background:#F8F4EE;border:1px solid #EDE5D8;border-radius:20px;padding:24px 26px;">

              <div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#8B6F52;">
                What happens next
              </div>

              <!-- step 1 -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:16px;">
                <tr>
                  <td valign="top" width="30" style="padding-top:0;">
                    <div style="width:24px;height:24px;border-radius:50%;background:#A38A70;text-align:center;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;color:#fff;line-height:24px;mso-line-height-rule:exactly;">1</div>
                  </td>
                  <td class="step-text" style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.65;color:#5F5A54;padding-left:10px;">
                    Create your Ittera account with this email — it links to your spot automatically.
                  </td>
                </tr>
              </table>

              <!-- step 2 -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:12px;">
                <tr>
                  <td valign="top" width="30" style="padding-top:0;">
                    <div style="width:24px;height:24px;border-radius:50%;background:#7A8B76;text-align:center;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;color:#fff;line-height:24px;mso-line-height-rule:exactly;">2</div>
                  </td>
                  <td class="step-text" style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.65;color:#5F5A54;padding-left:10px;">
                    We'll email you the moment beta opens for your position. No action needed until then.
                  </td>
                </tr>
              </table>

              <!-- step 3 -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:12px;">
                <tr>
                  <td valign="top" width="30" style="padding-top:0;">
                    <div style="width:24px;height:24px;border-radius:50%;background:#2B241E;text-align:center;font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;color:#C4A882;line-height:24px;mso-line-height-rule:exactly;">3</div>
                  </td>
                  <td class="step-text" style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.65;color:#5F5A54;padding-left:10px;">
                    Be among the first to test the product and vote on what we build next.
                  </td>
                </tr>
              </table>

              <!-- CTA — full width on mobile -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" class="cta-wrap" style="margin-top:22px;width:auto;">
                <tr>
                  <td class="cta-cell" style="border-radius:999px;background:#1A1614;">
                    <a href="https://ittera.in" class="cta-link" style="display:inline-block;padding:14px 28px;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.01em;color:#F4EFE8;text-decoration:none;border-radius:999px;mso-padding-alt:14px 28px;">
                      Go to Ittera &#8594;
                    </a>
                  </td>
                </tr>
              </table>

            </td>
          </tr>
        </table>

        <!-- sign-off -->
        <p class="signoff" style="margin:26px 0 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.7;color:#8B857D;">
          We're building this quietly and carefully. Excited to have you along.
          <br/>— The Ittera team
        </p>

      </td>
    </tr>

    <!-- footer -->
    <tr>
      <td class="footer-td" style="padding:18px 8px 0;text-align:center;font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:1.8;color:#A39A90;">
        You're receiving this because {escape(email)} joined the Ittera waitlist.
        <br/>No spam — one email now, one when beta opens.
        <br/><br/>
        <a href="https://ittera.in" style="color:#C4B49A;text-decoration:none;font-size:10px;">ittera.in</a>
        &nbsp;&middot;&nbsp;
        <a href="mailto:admin.ittera@gmail.com?subject=Unsubscribe&body=Please remove {escape(email)} from the Ittera waitlist." style="color:#C4B49A;text-decoration:none;font-size:10px;">unsubscribe</a>
      </td>
    </tr>

  </table>
</td></tr>
</table>

</body>
</html>"""

    message = EmailMessage()
    message["Subject"] = c["subject"]
    message["From"] = settings.MAIL_FROM
    message["To"] = email
    if settings.REPLY_TO_EMAIL:
        message["Reply-To"] = settings.REPLY_TO_EMAIL
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.replace(" ", ""))
            server.send_message(message)
    except Exception:
        logger.exception("Failed to send waitlist confirmation email to %s", email)
