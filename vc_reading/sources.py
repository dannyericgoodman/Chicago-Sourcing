"""Content sources: build the candidate pool of essays for each author and
fetch the full text of a chosen essay.

Two strategies are used, depending on the author's site:

* Paul Graham (paulgraham.com) — a static HTML index (`articles.html`) listing
  every essay as a relative `*.html` link. We scrape that index, and fetch each
  essay's plain-HTML body.
* Bill Gurley (abovethecrowd.com) and Andrew Chen (andrewchen.com) — both run
  WordPress, which exposes a clean JSON REST API at `/wp-json/wp/v2/posts`. We
  paginate that to enumerate the entire archive and to pull a post's full
  content, which is far more robust than scraping rendered HTML.

Everything degrades gracefully: if a live fetch fails, we fall back to a cached
pool (committed to the repo) and finally to a small embedded seed of verified
URLs so the newsletter can always go out.
"""

import logging
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# A real browser-ish UA — some of these sites sit behind Cloudflare and reject
# obviously-automated clients.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,application/xhtml+xml,*/*;q=0.8",
}

MAX_TEXT_CHARS = 16000  # plenty for high-quality takeaways; keeps token cost sane

# --------------------------------------------------------------------------- #
# Author configuration
# --------------------------------------------------------------------------- #
AUTHORS: List[Dict] = [
    {
        "key": "paul_graham",
        "name": "Paul Graham",
        "kind": "pg",
        "index_url": "https://paulgraham.com/articles.html",
        "base_url": "https://paulgraham.com/",
    },
    {
        "key": "bill_gurley",
        "name": "Bill Gurley",
        "kind": "wp",
        "api_url": "https://abovethecrowd.com/wp-json/wp/v2/posts",
    },
    {
        "key": "andrew_chen",
        "name": "Andrew Chen",
        "kind": "wp",
        "api_url": "https://andrewchen.com/wp-json/wp/v2/posts",
    },
]

# PG index links that are not essays.
PG_NON_ESSAYS = {
    "index.html", "articles.html", "rss.html", "bio.html", "books.html",
    "faq.html", "raq.html", "lib.html", "kedrosky.html", "say.html",
    "rss-full.html", "antispam.html", "spamfaq.html",
}

# Last-resort seed of verified URLs, used only if both the live pool build and
# the cache are unavailable. The live build normally supersedes this entirely.
SEED_POOL: Dict[str, List[Dict]] = {
    "paul_graham": [
        {"title": "Do Things that Don't Scale", "url": "https://paulgraham.com/ds.html"},
        {"title": "Startup = Growth", "url": "https://paulgraham.com/growth.html"},
        {"title": "How to Get Startup Ideas", "url": "https://paulgraham.com/startupideas.html"},
        {"title": "How to Make Wealth", "url": "https://paulgraham.com/wealth.html"},
        {"title": "Maker's Schedule, Manager's Schedule", "url": "https://paulgraham.com/makersschedule.html"},
        {"title": "Before the Startup", "url": "https://paulgraham.com/before.html"},
        {"title": "What Startups Are Really Like", "url": "https://paulgraham.com/really.html"},
        {"title": "Startups in 13 Sentences", "url": "https://paulgraham.com/13sentences.html"},
        {"title": "How Not to Die", "url": "https://paulgraham.com/die.html"},
        {"title": "Relentlessly Resourceful", "url": "https://paulgraham.com/relres.html"},
        {"title": "How to Disagree", "url": "https://paulgraham.com/disagree.html"},
        {"title": "Be Good", "url": "https://paulgraham.com/good.html"},
    ],
    "bill_gurley": [
        {"title": "All Markets Are Not Created Equal", "url": "https://abovethecrowd.com/2012/11/13/all-markets-are-not-created-equal-10-factors-to-consider-when-evaluating-digital-marketplaces/"},
    ],
    "andrew_chen": [
        {"title": "The Law of Shitty Clickthroughs", "url": "https://andrewchen.com/the-law-of-shitty-clickthroughs/"},
        {"title": "Growth Hacker is the new VP Marketing", "url": "https://andrewchen.com/how-to-be-a-growth-hacker-an-airbnbcraigslist-case-study/"},
    ],
}


def _get(url: str, **kwargs) -> Optional[requests.Response]:
    """GET with browser headers, light retry, and graceful failure."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30, **kwargs)
            if resp.status_code == 200:
                return resp
            logger.warning("GET %s -> HTTP %s", url, resp.status_code)
        except requests.RequestException as exc:
            logger.warning("GET %s failed (attempt %s): %s", url, attempt + 1, exc)
        time.sleep(2 ** attempt)
    return None


# --------------------------------------------------------------------------- #
# Pool building
# --------------------------------------------------------------------------- #
def _build_pg_pool(author: Dict) -> List[Dict]:
    resp = _get(author["index_url"])
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    pool, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # essays are relative links ending in .html, no scheme, no path
        if "/" in href or not href.endswith(".html") or href.startswith("http"):
            continue
        if href in PG_NON_ESSAYS:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        url = urljoin(author["base_url"], href)
        if url in seen:
            continue
        seen.add(url)
        pool.append({"title": title, "url": url})
    logger.info("Paul Graham pool: %d essays", len(pool))
    return pool


def _build_wp_pool(author: Dict) -> List[Dict]:
    pool, page = [], 1
    while page <= 30:  # safety cap: 30 * 100 = 3000 posts
        resp = _get(
            author["api_url"],
            params={"per_page": 100, "page": page, "_fields": "id,link,title"},
        )
        if not resp:
            break
        try:
            batch = resp.json()
        except ValueError:
            break
        if not isinstance(batch, list) or not batch:
            break
        for post in batch:
            title = BeautifulSoup(
                (post.get("title") or {}).get("rendered", ""), "html.parser"
            ).get_text(strip=True)
            link = post.get("link")
            if title and link:
                pool.append({"title": title, "url": link, "id": post.get("id"),
                             "api_url": author["api_url"]})
        if len(batch) < 100:
            break
        page += 1
    logger.info("%s pool: %d posts", author["name"], len(pool))
    return pool


def build_pool(author: Dict) -> List[Dict]:
    """Build the live candidate pool for an author, or [] on failure."""
    try:
        if author["kind"] == "pg":
            return _build_pg_pool(author)
        if author["kind"] == "wp":
            return _build_wp_pool(author)
    except Exception as exc:  # never let a source break the whole run
        logger.error("Pool build failed for %s: %s", author["name"], exc)
    return []


# --------------------------------------------------------------------------- #
# Full-text fetching
# --------------------------------------------------------------------------- #
def _clean(text: str) -> str:
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()[:MAX_TEXT_CHARS]


def _fetch_pg_text(entry: Dict) -> Optional[str]:
    resp = _get(entry["url"])
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    # PG essays render the body text inside the page; the dominant text block is
    # the essay itself. get_text on the body is noisy but good enough for an LLM.
    body = soup.body or soup
    return _clean(body.get_text("\n", strip=True))


def _fetch_wp_text(entry: Dict) -> Optional[str]:
    # Prefer the JSON API (robust against Cloudflare HTML challenges).
    if entry.get("id") and entry.get("api_url"):
        resp = _get(f"{entry['api_url']}/{entry['id']}",
                    params={"_fields": "content"})
        if resp:
            try:
                content = (resp.json().get("content") or {}).get("rendered", "")
                text = BeautifulSoup(content, "html.parser").get_text("\n", strip=True)
                if text:
                    return _clean(text)
            except ValueError:
                pass
    # Fall back to fetching the rendered page.
    resp = _get(entry["url"])
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    article = soup.find("article") or soup.body or soup
    return _clean(article.get_text("\n", strip=True))


def fetch_full_text(author: Dict, entry: Dict) -> Optional[str]:
    """Return the cleaned full text of an essay, or None if unavailable."""
    try:
        if author["kind"] == "pg":
            return _fetch_pg_text(entry)
        return _fetch_wp_text(entry)
    except Exception as exc:
        logger.error("Fetch failed for %s: %s", entry.get("url"), exc)
        return None
