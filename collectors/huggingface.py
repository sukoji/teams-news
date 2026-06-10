from __future__ import annotations

import requests

from collectors.base import DEFAULT_HEADERS, BaseCollector, NewsItem, parse_datetime
from utils.filters import summarize_text
from utils.media import is_valid_https_image_url
from datetime import timedelta

from utils.timezone import KST, now_kst

HF_DAILY_PAPERS_API = "https://huggingface.co/api/daily_papers"


class HuggingFaceCollector(BaseCollector):
    source_name = "Hugging Face Papers"

    def collect(self) -> list[NewsItem]:
        response = requests.get(
            HF_DAILY_PAPERS_API,
            headers=DEFAULT_HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        items: list[NewsItem] = []
        cutoff = now_kst() - timedelta(hours=48)

        for entry in payload:
            paper = entry.get("paper") or entry
            paper_id = paper.get("id")
            title = (paper.get("title") or "").strip()
            if not paper_id or not title:
                continue

            published_raw = (
                paper.get("submittedOnDailyAt")
                or paper.get("publishedAt")
                or entry.get("publishedAt")
            )
            published_at = parse_datetime(published_raw)
            if published_at is None:
                continue

            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=KST)

            if published_at < cutoff:
                continue

            raw_summary = (
                paper.get("ai_summary")
                or paper.get("summary")
                or entry.get("summary")
                or ""
            )
            summary = summarize_text(raw_summary) or title
            url = f"https://huggingface.co/papers/{paper_id}"
            thumbnail = entry.get("thumbnail") or paper.get("thumbnail")
            image_url = thumbnail if is_valid_https_image_url(thumbnail) else None
            if not image_url:
                candidate = (
                    f"https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/"
                    f"{paper_id}.png"
                )
                if is_valid_https_image_url(candidate):
                    image_url = candidate

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    url=url,
                    source=self.source_name,
                    published_at=published_at,
                    image_url=image_url,
                )
            )

        return items
