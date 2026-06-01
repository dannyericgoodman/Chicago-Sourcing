"""Email delivery + optional Notion archive.

Two interchangeable email backends, chosen by which secret is set:
  * Resend  (recommended) — one API key, sends over HTTPS, no App Password / 2FA.
    With the default onboarding@resend.dev sender you can email your *own*
    address with zero domain setup. Set RESEND_API_KEY.
  * Gmail SMTP — set GMAIL_ADDRESS + a 16-char App Password.

`send_newsletter` returns True only when the provider accepted the message.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


def _recipient() -> str:
    return (os.getenv("NEWSLETTER_TO")
            or os.getenv("GMAIL_ADDRESS")
            or "danny.eric.goodman@gmail.com").strip()


def _send_resend(subject: str, html_body: str, text_body: str) -> bool:
    key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("RESEND_FROM", "The VC Reading Room <onboarding@resend.dev>").strip()
    to = [r.strip() for r in _recipient().split(",")]
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"from": sender, "to": to, "subject": subject,
                  "html": html_body, "text": text_body},
            timeout=30,
        )
        if resp.status_code in (200, 201):
            logger.info("Email sent via Resend to %s", to)
            return True
        logger.error("Resend send FAILED: HTTP %s — %s", resp.status_code, resp.text[:400])
    except Exception as exc:
        logger.error("Resend send FAILED: %s", exc)
    return False


def _send_gmail(subject: str, html_body: str, text_body: str) -> bool:
    user = (os.getenv("GMAIL_ADDRESS") or "").strip()
    password = (os.getenv("GMAIL_APP_PASSWORD") or "").replace(" ", "")  # strip the displayed spaces
    recipient = _recipient()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"The VC Reading Room <{user}>"
    msg["To"] = recipient
    msg["Reply-To"] = user
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(user, password)
            server.sendmail(user, [r.strip() for r in recipient.split(",")], msg.as_string())
        logger.info("Email sent via Gmail to %s", recipient)
        return True
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Gmail auth FAILED (need 2FA + a valid 16-char App Password): %s", exc)
    except Exception as exc:
        logger.error("Gmail send FAILED: %s", exc)
    return False


def send_newsletter(subject: str, html_body: str, text_body: str) -> bool:
    """Try each configured backend until one accepts the message.

    Resend is tried first (if a key is set), then Gmail SMTP. Whichever succeeds
    wins; we never send twice.
    """
    tried = []
    if os.getenv("RESEND_API_KEY"):
        tried.append("Resend")
        if _send_resend(subject, html_body, text_body):
            return True
    if os.getenv("GMAIL_ADDRESS") and os.getenv("GMAIL_APP_PASSWORD"):
        tried.append("Gmail")
        if _send_gmail(subject, html_body, text_body):
            return True
    if not tried:
        logger.error("Email NOT sent: configure RESEND_API_KEY (recommended) or "
                     "GMAIL_ADDRESS + GMAIL_APP_PASSWORD.")
    else:
        logger.error("Email NOT sent: all configured backends failed (%s).",
                     ", ".join(tried))
    return False


# --------------------------------------------------------------------------- #
# Optional Notion archive (best-effort; skipped if secrets absent)
# --------------------------------------------------------------------------- #
def _rich(text: str) -> List[Dict]:
    return [{"type": "text", "text": {"content": text[:1900]}}]


def _issue_blocks(issues: List[Dict]) -> List[Dict]:
    blocks: List[Dict] = []
    for it in issues:
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": f"{it['author']}: {it['title']}",
                                                    "link": {"url": it["url"]}}}]}})
        blocks.append({"object": "block", "type": "quote",
                       "quote": {"rich_text": _rich(it["one_liner"])}})
        for t in it["takeaways"]:
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": _rich(t)}})
        if it.get("investor_angle"):
            blocks.append({"object": "block", "type": "callout", "callout": {
                "icon": {"emoji": "💡"}, "rich_text": _rich("Investor angle: " + it["investor_angle"])}})
        blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks


def archive_to_notion(issues: List[Dict], date_str: str, iso_date: Optional[str] = None) -> None:
    token, db_id = os.getenv("NOTION_API_KEY"), os.getenv("NOTION_DATABASE_ID")
    if not token or not db_id:
        return
    props: Dict = {
        "Name": {"title": [{"text": {"content": f"VC Reading — {date_str}"}}]},
        "Authors": {"rich_text": _rich(", ".join(it["author"] for it in issues))},
    }
    if iso_date:
        props["Date"] = {"date": {"start": iso_date}}
    try:
        resp = requests.post("https://api.notion.com/v1/pages",
                             headers={"Authorization": f"Bearer {token}",
                                      "Notion-Version": "2022-06-28",
                                      "Content-Type": "application/json"},
                             json={"parent": {"database_id": db_id}, "properties": props,
                                   "children": _issue_blocks(issues)}, timeout=30)
        if resp.status_code == 200:
            logger.info("Archived to Notion.")
        else:
            logger.warning("Notion archive failed: HTTP %s — %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Notion archive error: %s", exc)
