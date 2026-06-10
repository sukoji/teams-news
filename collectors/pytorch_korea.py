from __future__ import annotations

import feedparser
import requests

from collectors.base import DEFAULT_HEADERS, BaseCollector, NewsItem, parse_datetime
from utils.filters import summarize_text
from utils.media import extract_image_from_feed_entry
from datetime import timedelta

from utils.timezone import KST, now_kst

# 읽을거리&정보공유 board (Discourse category slug: news, id: 14)
PYTORCH_KOREA_BOARD_URL = "https://discuss.pytorch.kr/c/news/14"
PYTORCH_KOREA_RSS_URL = "https://discuss.pytorch.kr/c/news/14.rss"


class PyTorchKoreaCollector(BaseCollector):
    source_name = "PyTorch Korea"

    def collect(self) -> list[NewsItem]:
        response = requests.get(
            PYTORCH_KOREA_RSS_URL,
            headers={
                **DEFAULT_HEADERS,
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
            timeout=30,
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        items: list[NewsItem] = []
        cutoff = now_kst() - timedelta(hours=24)

        for index, entry in enumerate(feed.entries):
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

            # RSS order reflects category prominence; earlier entries rank higher.
            feed_rank = max(0, 100 - index)

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    url=link,
                    source=self.source_name,
                    published_at=published_at,
                    popularity=feed_rank,
                    image_url=extract_image_from_feed_entry(entry),
                )
            )

        return items
