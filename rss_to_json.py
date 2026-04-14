"""
RSS ingestion entry point.
Fetches all registered sources and writes unified article list to data/rss_articles.json.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.ingestion.rss_ingestor import ingest_all

OUTPUT_PATH = "data/rss_articles.json"

if __name__ == "__main__":
    print("Starting multi-source RSS ingestion...\n")
    articles = ingest_all(verbose=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(articles)} articles to {OUTPUT_PATH}")

    if len(articles) == 0:
        print("WARNING: No articles saved!")
        sys.exit(1)
