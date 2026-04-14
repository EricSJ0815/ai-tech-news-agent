"""
Article-level cache backed by data/cache.json.

Structure:
{
  "summary": { "<cache_key>": { ...summarized fields } },
  "insight":  { "<cache_key>": "insight text" }
}

Cache key priority:
  1. article["link"]  (canonical URL)
  2. title[:80] + "|" + source  (fallback when link is empty)
"""

import json
import os

from src.utils.logger import get_logger

_log = get_logger()

_CACHE_PATH = os.path.join("data", "cache.json")


def _load() -> dict:
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _log.warning(f"[cache] 读取失败，重置为空: {e}")
    return {"summary": {}, "insight": {}}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log.warning(f"[cache] 写入失败: {e}")


def make_key(link: str, title: str = "", source: str = "") -> str:
    """Return the canonical cache key for an article."""
    if link and link.strip():
        return link.strip()
    return (title[:80] + "|" + source).strip()


class ArticleCache:
    """Thread-unsafe but sufficient for single-process pipeline use."""

    def __init__(self):
        self._data = _load()

    def get(self, namespace: str, key: str):
        """Return cached value or None on miss.
        Always reloads from disk so stale in-memory state never hides a hit.
        """
        self._data = _load()
        value = self._data.get(namespace, {}).get(key)
        if value is not None:
            _log.info(f"[cache] hit  | ns={namespace} key={key[:60]}")
            return value
        _log.info(f"[cache] miss | ns={namespace} key={key[:60]}")
        return None

    def set(self, namespace: str, key: str, value) -> None:
        """Store value and persist to disk.
        Reloads from disk before writing to merge changes from other instances
        (e.g., summarize_agent and insight_agent are separate instances).
        """
        self._data = _load()  # merge-safe read-before-write
        if namespace not in self._data:
            self._data[namespace] = {}
        self._data[namespace][key] = value
        _save(self._data)

    def stats(self) -> dict:
        """Return count of cached entries per namespace."""
        return {ns: len(entries) for ns, entries in self._data.items()}
