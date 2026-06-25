from __future__ import annotations

import logging
import os
import re
import time
from datetime import timedelta

import feedparser
import requests

from collectors.base import DEFAULT_HEADERS, BaseCollector, NewsItem, parse_datetime
from utils.filters import summarize_text
from utils.timezone import KST, now_kst

logger = logging.getLogger(__name__)

ENABLE_GEEKNEWS_ENGAGEMENT = os.getenv(
    "ENABLE_GEEKNEWS_ENGAGEMENT", "false"
).lower() in {"1", "true", "yes"}

GEEKNEWS_TOPIC_FETCH_DELAY_SEC = 0.3

GEEKNEWS_RSS_URLS = (
    "https://news.hada.io/rss/news",
    "https://news.hada.io/rss",
)


def _topic_id_from_url(url: str) -> str | None:
    match = re.search(r"[?&]id=(\d+)", url)
    return match.group(1) if match else None


def _fetch_topic_engagement(topic_id: str) -> tuple[int, int]:
    """Return GeekNews topic points and comment count."""
    try:
        response = requests.get(
            f"https://news.hada.io/topic?id={topic_id}",
            headers=DEFAULT_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        text = response.text
        points_match = re.search(rf"<span id='tp{topic_id}'>(\d+)</span>P", text)
        comments_match = re.search(r'"commentCount":\s*(\d+)', text)
        points = int(points_match.group(1)) if points_match else 0
        comments = int(comments_match.group(1)) if comments_match else 0
        return points, comments
    except Exception:
        logger.debug("GeekNews engagement fetch failed for topic %s", topic_id)
        return 0, 0


def _attach_geeknews_engagement(items: list[NewsItem]) -> None:
    if not ENABLE_GEEKNEWS_ENGAGEMENT or not items:
        return

    topic_ids = [_topic_id_from_url(item.url) for item in items]
    engagement: dict[str, tuple[int, int]] = {}

    for topic_id in topic_ids:
        if not topic_id:
            continue
        engagement[topic_id] = _fetch_topic_engagement(topic_id)
        time.sleep(GEEKNEWS_TOPIC_FETCH_DELAY_SEC)

    for item, topic_id in zip(items, topic_ids):
        if not topic_id:
            continue
        points, comments = engagement.get(topic_id, (0, 0))
        item.popularity = points * 5 + comments * 3


class GeekNewsCollector(BaseCollector):
    source_name = "GeekNews"

    def collect(self) -> list[NewsItem]:
        last_error: Exception | None = None

        for rss_url in GEEKNEWS_RSS_URLS:
            try:
                response = requests.get(
                    rss_url,
                    headers={
                        **DEFAULT_HEADERS,
                        "Accept": "application/rss+xml, application/xml, text/xml, */*",
                    },
                    timeout=30,
                )
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                if feed.entries:
                    return self._parse_feed(feed)
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        return []

    def _parse_feed(self, feed: feedparser.FeedParserDict) -> list[NewsItem]:
        items: list[NewsItem] = []
        cutoff = now_kst() - timedelta(hours=24)

        for entry in feed.entries:
            published_at = parse_datetime(
                getattr(entry, "published", None) or getattr(entry, "updated", None)
            )
            if published_at is None:
                continue

            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=KST)

            if published_at < cutoff:
                continue

            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue

            raw_summary = (
                entry.get("summary")
                or entry.get("description")
                or entry.get("content", [{}])[0].get("value", "")
            )
            summary = summarize_text(raw_summary) or title

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    url=link,
                    source=self.source_name,
                    published_at=published_at,
                )
            )

        _attach_geeknews_engagement(items)
        return items
