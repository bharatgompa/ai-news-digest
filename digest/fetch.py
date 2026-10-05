"""Collect recent items from RSS feeds and YouTube channel feeds."""

import calendar
import html
import logging
import re
import time
from dataclasses import dataclass

import feedparser

log = logging.getLogger(__name__)

YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
USER_AGENT = "Mozilla/5.0 (ai-news-digest; +https://github.com)"


@dataclass
class Item:
    id: int
    title: str
    url: str
    source: str
    category: str
    published: float  # unix timestamp
    snippet: str


def _clean(text: str, limit: int) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:limit]


def _published_ts(entry) -> float | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return calendar.timegm(parsed) if parsed else None


def _read_feed(name: str, url: str, category: str, cutoff: float, limit: int) -> list[dict]:
    feed = feedparser.parse(url, agent=USER_AGENT)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"unreadable feed: {feed.bozo_exception}")

    items = []
    for entry in feed.entries:
        ts = _published_ts(entry)
        if ts is None or ts < cutoff:
            continue
        snippet = entry.get("summary") or ""
        # YouTube puts the description under media_description
        if not snippet and entry.get("media_description"):
            snippet = entry["media_description"]
        items.append({
            "title": _clean(entry.get("title", ""), 200),
            "url": entry.get("link", ""),
            "source": name,
            "category": category,
            "published": ts,
            "snippet": _clean(snippet, 500),
        })
        if len(items) >= limit:
            break
    return items


def collect(config: dict) -> tuple[list[Item], list[str]]:
    """Return (items, failed_source_names)."""
    settings = config["settings"]
    cutoff = time.time() - settings["lookback_hours"] * 3600
    per_feed = settings["max_items_per_feed"]

    sources = [(f["name"], f["url"], f["category"]) for f in config.get("feeds", [])]
    sources += [
        (c["name"], YOUTUBE_FEED.format(c["channel_id"]), "youtube")
        for c in config.get("youtube_channels") or []
    ]

    raw, failed = [], []
    for name, url, category in sources:
        try:
            got = _read_feed(name, url, category, cutoff, per_feed)
            log.info("%-28s %d items", name, len(got))
            raw.extend(got)
        except Exception as e:  # one bad feed must not kill the run
            log.warning("%-28s FAILED: %s", name, e)
            failed.append(name)

    # Drop duplicate links (HN often links the same article another feed has)
    seen, unique = set(), []
    for r in sorted(raw, key=lambda r: r["published"], reverse=True):
        key = r["url"].split("?")[0].rstrip("/")
        if key and key not in seen:
            seen.add(key)
            unique.append(r)

    unique = unique[: settings["max_items_total"]]
    return [Item(id=i, **r) for i, r in enumerate(unique)], failed
