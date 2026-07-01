from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

BOT_USER_AGENT = (
    "PIAI-TeamsNews/1.0 (+https://sukoji.github.io/teams-news/about)"
)

DEFAULT_HEADERS = {
    "User-Agent": BOT_USER_AGENT,
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    score: float = 0.0
    popularity: int = 0
    upvotes: int = 0
    importance_score: float = 0.0
    matched_keywords: list[str] = field(default_factory=list)
    image_url: str | None = None
    title_ko: str | None = None
    summary_ko: str | None = None


class BaseCollector(ABC):
    source_name: str

    @abstractmethod
    def collect(self) -> list[NewsItem]:
        """Fetch and return normalized news items."""

    def safe_collect(self) -> list[NewsItem]:
        try:
            items = self.collect()
            logger.info("[%s] collected %d items", self.source_name, len(items))
            return items
        except Exception:
            logger.exception("[%s] collection failed", self.source_name)
            return []


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    from dateutil import parser as date_parser

    try:
        return date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
