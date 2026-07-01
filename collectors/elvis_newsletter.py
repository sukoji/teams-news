from __future__ import annotations

from datetime import timedelta

import feedparser
import requests

from collectors.base import DEFAULT_HEADERS, BaseCollector, NewsItem, parse_datetime
from utils.filters import summarize_text
from utils.timezone import KST, now_kst

# Elvis AI Newsletter (Substack) public RSS — robots.txt allows /feed (not /feed/private)
ELVIS_NEWSLETTER_RSS_URL = "https://nlp.elvissaravia.com/feed"


class ElvisNewsletterCollector(BaseCollector):
    source_name = "Elvis AI Newsletter"

    def collect(self) -> list[NewsItem]:
        response = requests.get(
            ELVIS_NEWSLETTER_RSS_URL,
            headers={
                **DEFAULT_HEADERS,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            },
            timeout=30,
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        items: list[NewsItem] = []
        cutoff = now_kst() - timedelta(hours=168)

        for rank, entry in enumerate(feed.entries):
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
                    popularity=max(0, 100 - rank),
                )
            )

        return items
