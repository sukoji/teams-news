from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    score: int = 0
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
