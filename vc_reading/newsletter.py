"""Orchestrator + CLI for the daily VC reading newsletter.

  python -m vc_reading.newsletter            # full run (build, summarize, send)
  python -m vc_reading.newsletter --dry-run  # no email/Notion; writes preview.html
  python -m vc_reading.newsletter --refresh   # force-rebuild the candidate pool

State is kept in two small JSON files (committed back by CI so progress
persists across the ephemeral runner):
  vc_reading/data/pool_cache.json  — the candidate pool per author
  vc_reading/data/state.json       — URLs already sent, for no-repeat rotation
"""

import argparse
import json
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from anthropic import Anthropic

from . import curriculum, deliver, render, sources, summarize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("vc_reading")

DATA_DIR = Path(__file__).parent / "data"
POOL_CACHE = DATA_DIR / "pool_cache.json"
STATE_FILE = DATA_DIR / "state.json"
POOL_MAX_AGE_DAYS = 7  # rebuild the pool at most weekly


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def get_pool(force_refresh: bool) -> Dict[str, List[Dict]]:
    """Return {author_key: [entries]}, rebuilding from the web when stale."""
    cache = _load_json(POOL_CACHE, {})
    built_at = cache.get("_built_at")
    fresh = False
    if built_at:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(built_at)).days
        fresh = age < POOL_MAX_AGE_DAYS

    pools = cache.get("pools", {})
    if force_refresh or not fresh or not pools:
        logger.info("Building candidate pool from source sites...")
        new_pools = {}
        for author in sources.AUTHORS:
            live = sources.build_pool(author)
            if live:
                new_pools[author["key"]] = live
            else:  # keep whatever we had, else fall back to the seed
                logger.warning("Falling back for %s (live build empty).", author["name"])
                new_pools[author["key"]] = pools.get(
                    author["key"]) or sources.SEED_POOL.get(author["key"], [])
        pools = new_pools
        _save_json(POOL_CACHE, {
            "_built_at": datetime.now(timezone.utc).isoformat(),
            "pools": pools,
        })
    else:
        logger.info("Using cached pool (built %s).", built_at)
    return pools


def _pick_for_author(key: str, pool: List[Dict], sent_urls: set) -> Dict:
    """Choose the next essay for one author.

    1. Walk the curated curriculum in order and take the first entry not yet
       sent (using the live archive's authoritative URL when matched).
    2. Once the curriculum is exhausted, dip into the rest of the archive
       (random, for variety) for breadth.
    """
    for entry in curriculum.CURRICULUM.get(key, []):
        match = curriculum.match_in_pool(entry, pool)
        url = match.get("url") or entry.get("url")
        if url and url not in sent_urls:
            chosen = match or {"title": entry["title"], "url": entry["url"]}
            chosen = dict(chosen)
            chosen["curated"] = True
            return chosen

    tail = [e for e in pool if e["url"] not in sent_urls]
    if tail:
        choice = dict(random.choice(tail))
        choice["curated"] = False
        return choice
    return {}


def select_today(pools: Dict[str, List[Dict]], state: Dict) -> List[Dict]:
    """Pick one essay per author, advancing the curriculum; recycle when done."""
    sent = state.setdefault("sent", {})
    selections = []
    for author in sources.AUTHORS:
        key = author["key"]
        pool = pools.get(key, []) or sources.SEED_POOL.get(key, [])
        if not pool:
            logger.error("No essays available for %s; skipping.", author["name"])
            continue
        sent_urls = set(sent.get(key, []))
        choice = _pick_for_author(key, pool, sent_urls)
        if not choice:  # everything seen — start the journey over
            logger.info("%s fully read — recycling from the top.", author["name"])
            sent[key] = []
            choice = _pick_for_author(key, pool, set())
        if not choice:
            logger.error("Still nothing for %s; skipping.", author["name"])
            continue
        stage = "curated" if choice.get("curated") else "archive"
        logger.info("%s [%s]: %s", author["name"], stage, choice["title"])
        sent.setdefault(key, [])
        if choice["url"] not in sent[key]:
            sent[key].append(choice["url"])
        selections.append({"author": author, "entry": choice})
    return selections


def build_issue(selections: List[Dict], client: Anthropic) -> List[Dict]:
    issue = []
    for sel in selections:
        author, entry = sel["author"], sel["entry"]
        logger.info("Summarizing %s — %s", author["name"], entry["title"])
        text = sources.fetch_full_text(author, entry)
        summ = summarize.summarize(
            author["name"], entry["title"], text, entry["url"], client=client)
        issue.append({
            "author": author["name"],
            "title": entry["title"],
            "url": entry["url"],
            **summ,
        })
    return issue


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Daily VC reading newsletter")
    parser.add_argument("--dry-run", action="store_true",
                        help="skip email/Notion; write a local preview.html")
    parser.add_argument("--refresh", action="store_true",
                        help="force-rebuild the candidate pool from the web")
    args = parser.parse_args(argv)

    date_str = datetime.now().strftime("%A, %B %-d, %Y")

    pools = get_pool(force_refresh=args.refresh)
    state = _load_json(STATE_FILE, {"sent": {}})
    selections = select_today(pools, state)
    if not selections:
        logger.error("Nothing selected — aborting.")
        return 1

    client = None
    if not args.dry_run or os.getenv("ANTHROPIC_API_KEY"):
        if os.getenv("ANTHROPIC_API_KEY"):
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    if client is None:
        logger.warning("ANTHROPIC_API_KEY not set — using fallback takeaways.")

    issue = build_issue(selections, client)
    html_body = render.render_html(issue, date_str)
    text_body = render.render_text(issue, date_str)
    subject = f"📚 The VC Reading Room — {datetime.now().strftime('%b %-d')}"

    if args.dry_run:
        preview = DATA_DIR / "preview.html"
        _save_json(STATE_FILE, state)  # persist selection even in dry run
        preview.parent.mkdir(parents=True, exist_ok=True)
        preview.write_text(html_body)
        print("\n" + text_body)
        logger.info("Dry run complete. Preview written to %s", preview)
        return 0

    deliver.send_email(subject, html_body, text_body)
    deliver.archive_to_notion(issue, date_str, iso_date=datetime.now().strftime("%Y-%m-%d"))
    _save_json(STATE_FILE, state)
    logger.info("Done. Sent %d essays.", len(issue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
