"""Delivery channels: Gmail SMTP email and a per-day Notion archive page.

Both are optional and degrade gracefully — if the relevant environment
variables are missing, the channel is skipped with a log message rather than
failing the run.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

NOTION_VERSION = "2022-06-28"


# --------------------------------------------------------------------------- #
# Email (Gmail SMTP)
# --------------------------------------------------------------------------- #
def send_email(subject: str, html_body: str, text_body: str) -> bool:
    user = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    # Delivery target: explicit NEWSLETTER_TO wins, then the sending account,
    # and finally the owner's inbox as a safe default.
    recipient = os.getenv("NEWSLETTER_TO") or user or "danny.eric.goodman@gmail.com"

    if not user or not password:
        logger.warning("Email skipped: GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"The VC Reading Room <{user}>"
    msg["To"] = recipient
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(user, password)
            server.sendmail(user, [r.strip() for r in recipient.split(",")], msg.as_string())
        logger.info("Email sent to %s", recipient)
        return True
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return False


# --------------------------------------------------------------------------- #
# Notion archive
# --------------------------------------------------------------------------- #
def _rich(text: str) -> List[Dict]:
    # Notion caps rich_text content at 2000 chars per object.
    return [{"type": "text", "text": {"content": text[:1900]}}]


def _issue_blocks(issues: List[Dict]) -> List[Dict]:
    blocks: List[Dict] = []
    for it in issues:
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{
                "type": "text",
                "text": {"content": f"{it['author']}: {it['title']}",
                         "link": {"url": it["url"]}},
            }]},
        })
        blocks.append({
            "object": "block", "type": "quote",
            "quote": {"rich_text": _rich(it["one_liner"])},
        })
        for t in it["takeaways"]:
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich(t)},
            })
        if it.get("investor_angle"):
            blocks.append({
                "object": "block", "type": "callout",
                "callout": {
                    "icon": {"emoji": "💡"},
                    "rich_text": _rich("Investor angle: " + it["investor_angle"]),
                },
            })
        blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks


def archive_to_notion(issues: List[Dict], date_str: str,
                      iso_date: Optional[str] = None) -> Optional[str]:
    token = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not token or not db_id:
        logger.warning("Notion archive skipped: NOTION_API_KEY / NOTION_DATABASE_ID not set.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    properties: Dict = {
        "Name": {"title": [{"text": {"content": f"VC Reading — {date_str}"}}]},
        "Authors": {"rich_text": _rich(", ".join(it["author"] for it in issues))},
    }
    if iso_date:
        properties["Date"] = {"date": {"start": iso_date}}
    payload = {
        "parent": {"database_id": db_id},
        "properties": properties,
        "children": _issue_blocks(issues),
    }
    try:
        resp = requests.post("https://api.notion.com/v1/pages",
                             headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            url = resp.json().get("url")
            logger.info("Archived to Notion: %s", url)
            return url
        logger.error("Notion archive failed: HTTP %s — %s", resp.status_code, resp.text[:300])
    except Exception as exc:
        logger.error("Notion archive error: %s", exc)
    return None
