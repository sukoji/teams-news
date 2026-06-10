from __future__ import annotations

from datetime import timedelta

import feedparser
import requests

from collectors.base import DEFAULT_HEADERS, BaseCollector, NewsItem, parse_datetime
from utils.filters import summarize_text
from utils.media import extract_image_from_feed_entry
from utils.timezone import KST, now_kst

GEEKNEWS_RSS_URLS = (
    "https://news.hada.io/rss/news",
    "https://news.hada.io/rss",
)


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
                    image_url=extract_image_from_feed_entry(entry),
                )
            )

        return items
