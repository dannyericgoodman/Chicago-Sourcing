"""Daily VC reading newsletter — build and email one curated essay each from
Paul Graham, Bill Gurley, and Andrew Chen, with Claude-written takeaways.

  python -m vc_reading.newsletter            # build + send
  python -m vc_reading.newsletter --dry-run  # no send; write preview.html
  python -m vc_reading.newsletter --force    # send even if already sent today

Which essay goes out is deterministic by date (no scraping needed to choose), so
the only state we keep is a one-line `last_sent_date` to de-duplicate when the
workflow fires several times for reliability.
"""

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from anthropic import Anthropic

from . import deliver, essays, fetch, render, summarize

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logger = logging.getLogger("vc_reading")

STATE_FILE = Path(__file__).parent / "data" / "state.json"


def _load_state() -> Dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def _save_state(state: Dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def select_today() -> List[Dict]:
    """Pick one essay per author, advancing through the curated list by date."""
    idx = date.today().toordinal()
    picks = []
    for author in essays.AUTHORS:
        lst = author["essays"]
        entry = lst[idx % len(lst)]
        logger.info("%s: %s", author["name"], entry["title"])
        picks.append({"author": author, "entry": entry})
    return picks


def build_issue(picks: List[Dict], client: Optional[Anthropic]) -> List[Dict]:
    issue = []
    for p in picks:
        author, entry = p["author"], p["entry"]
        text = fetch.fetch_text(author, entry["url"])
        summ = summarize.summarize(author["name"], entry["title"], text, entry["url"], client=client)
        issue.append({"author": author["name"], "title": entry["title"],
                      "url": entry["url"], **summ})
    return issue


def _preflight() -> None:
    have_resend = bool(os.getenv("RESEND_API_KEY"))
    have_gmail = bool(os.getenv("GMAIL_ADDRESS") and os.getenv("GMAIL_APP_PASSWORD"))
    logger.info("Preflight: ANTHROPIC_API_KEY=%s | RESEND_API_KEY=%s | "
                "GMAIL creds=%s | recipient=%s | NOTION=%s",
                "SET" if os.getenv("ANTHROPIC_API_KEY") else "MISSING",
                "SET" if have_resend else "MISSING",
                "SET" if have_gmail else "MISSING",
                deliver._recipient(),
                "SET" if (os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID")) else "off")
    if not have_resend and not have_gmail:
        logger.error("No email backend configured — set RESEND_API_KEY (recommended) "
                     "or GMAIL_ADDRESS + GMAIL_APP_PASSWORD.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Daily VC reading newsletter")
    parser.add_argument("--dry-run", action="store_true", help="no send; write preview.html")
    parser.add_argument("--force", action="store_true", help="send even if already sent today")
    args = parser.parse_args(argv)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state = _load_state()

    if not args.dry_run:
        _preflight()
        if not args.force and state.get("last_sent_date") == today:
            logger.info("Already sent today (%s) — nothing to do.", today)
            return 0

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if os.getenv("ANTHROPIC_API_KEY") else None
    if client is None:
        logger.warning("ANTHROPIC_API_KEY not set — takeaways will be placeholders.")

    issue = build_issue(select_today(), client)
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    html_body = render.render_html(issue, date_str)
    text_body = render.render_text(issue, date_str)
    subject = f"📚 The VC Reading Room — {datetime.now().strftime('%b %d')}"

    if args.dry_run:
        preview = STATE_FILE.parent / "preview.html"
        preview.parent.mkdir(parents=True, exist_ok=True)
        preview.write_text(html_body)
        print("\n" + text_body)
        logger.info("Dry run complete. Preview at %s", preview)
        return 0

    if not deliver.send_newsletter(subject, html_body, text_body):
        logger.error("Email FAILED — see the error above. Not marking today as sent; "
                     "the next run will retry.")
        return 1

    deliver.archive_to_notion(issue, date_str, iso_date=datetime.now().strftime("%Y-%m-%d"))
    state["last_sent_date"] = today
    _save_state(state)
    logger.info("Done — emailed %d essays.", len(issue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
