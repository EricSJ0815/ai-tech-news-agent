"""
RSS ingestion module — multi-source fetch, parse, normalize, dedupe.

Article schema (compatible with existing pipeline):
    {
        "title":     str,
        "summary":   str,
        "link":      str,
        "source":    str,
        "published": str,   # empty string if unavailable
    }
"""

import json
import os
import re
import time
from datetime import datetime

import feedparser

from src.pipeline.dedupe_articles import dedupe_articles
from src.utils.logger import get_logger


# ── Source registry ────────────────────────────────────────────────────
# Each entry: (display_name, rss_url, max_entries)

SOURCE_REGISTRY = [
    ("TechCrunch",      "https://techcrunch.com/feed/",                              15),
    ("The Verge",       "https://www.theverge.com/rss/index.xml",                    15),
    ("VentureBeat AI",  "https://venturebeat.com/category/ai/feed/",                 15),
    ("Ars Technica",    "https://feeds.arstechnica.com/arstechnica/index",            15),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/",                    10),
    ("Wired",           "https://www.wired.com/feed/rss",                             10),
    ("AI News",         "https://artificialintelligence-news.com/feed/",             10),
    ("ZDNet AI",        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", 10),
]


# ── Fetch ──────────────────────────────────────────────────────────────

def fetch_feed(name: str, url: str) -> feedparser.FeedParserDict | None:
    """Fetch a single RSS feed. Returns parsed feed or None on failure."""
    log = get_logger()
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        if feed.bozo and not feed.entries:
            log.warning(f"[fetch] {name}: feed error — {feed.bozo_exception}")
            return None
        return feed
    except Exception as e:
        log.error(f"[fetch] {name}: exception — {e}")
        return None


# ── Parse & normalize ─────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def parse_entries(feed: feedparser.FeedParserDict, source_name: str, max_entries: int) -> list[dict]:
    """Normalize feed entries into unified article dicts."""
    articles = []
    for entry in feed.entries[:max_entries]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue

        summary = entry.get("summary") or ""
        if not summary and entry.get("content"):
            summary = entry["content"][0].get("value", "")
        summary = _clean_html(summary)

        articles.append({
            "title":     title,
            "summary":   summary,
            "link":      entry.get("link") or "",
            "source":    source_name,
            "published": entry.get("published") or entry.get("updated") or "",
        })
    return articles


# ── Raw save ──────────────────────────────────────────────────────────

def _save_raw(articles: list[dict]) -> str | None:
    """
    Save normalized articles to data/raw/YYYY-MM-DD_articles.json.
    Returns the path on success, None on failure (warning logged, no raise).
    """
    log = get_logger()
    date_str = datetime.now().strftime("%Y-%m-%d")
    raw_dir = "data/raw"
    path = f"{raw_dir}/{date_str}_articles.json"
    try:
        os.makedirs(raw_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        log.info(f"[raw] saved {len(articles)} articles → {path}")
        return path
    except Exception as e:
        log.warning(f"[raw] save failed: {e}")
        return None


# ── Main entry point ──────────────────────────────────────────────────

def ingest_all(verbose: bool = True, save_raw: bool = True) -> list[dict]:
    """
    Fetch all sources, normalize, dedupe, save raw, and return article list.
    A single source failure never crashes the run.
    """
    log = get_logger()
    run_start = time.time()

    log.info("=" * 50)
    log.info(f"[ingestion] start — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_articles: list[dict] = []
    source_results: list[dict] = []

    for name, url, max_entries in SOURCE_REGISTRY:
        log.info(f"[fetch] {name} ...")
        feed = fetch_feed(name, url)

        if feed is None:
            source_results.append({"source": name, "status": "FAILED", "count": 0})
            log.warning(f"[fetch] {name}: FAILED — skipping")
            continue

        articles = parse_entries(feed, name, max_entries)
        source_results.append({"source": name, "status": "OK", "count": len(articles)})
        log.info(f"[fetch] {name}: OK — {len(articles)} entries")
        all_articles.extend(articles)

    raw_total = len(all_articles)
    deduped = dedupe_articles(all_articles)
    deduped_total = len(deduped)

    # Raw save (non-blocking)
    if save_raw:
        _save_raw(deduped)

    # ── Run summary ───────────────────────────────────────────────────
    ok_sources  = [r for r in source_results if r["status"] == "OK"]
    fail_sources = [r for r in source_results if r["status"] == "FAILED"]
    elapsed = round(time.time() - run_start, 1)

    log.info("-" * 50)
    log.info("[ingestion] SOURCE HEALTH:")
    for r in source_results:
        status_icon = "✓" if r["status"] == "OK" else "✗"
        log.info(f"  {status_icon}  {r['source']:<20} {r['count']:>3} articles  [{r['status']}]")

    log.info("-" * 50)
    log.info(f"[ingestion] sources  : {len(ok_sources)} ok / {len(fail_sources)} failed")
    log.info(f"[ingestion] raw total: {raw_total}")
    log.info(f"[ingestion] deduped  : {deduped_total}")
    log.info(f"[ingestion] elapsed  : {elapsed}s")
    log.info("=" * 50)

    return deduped
