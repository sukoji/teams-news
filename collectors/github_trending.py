from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import quote

import requests

from collectors.base import DEFAULT_HEADERS, BaseCollector, NewsItem, parse_datetime
from utils.filters import summarize_text
from utils.timezone import KST, now_kst

logger = logging.getLogger(__name__)

# GitHub Search API (api.github.com) — no auth needed for low-volume daily use.
GITHUB_SEARCH_API = "https://api.github.com/search/repositories"

ML_SEARCH_QUERIES: tuple[str, ...] = (
    "stars:>20 created:>{date} topic:machine-learning",
    "stars:>20 created:>{date} topic:deep-learning",
    "stars:>15 created:>{date} topic:llm",
    "stars:>15 created:>{date} topic:pytorch",
    "stars:>15 created:>{date} topic:generative-ai",
)

# Established mega-repos are not "trending" news.
MAX_ESTABLISHED_STARS = 5000


class GitHubTrendingCollector(BaseCollector):
    source_name = "GitHub Trending"

    def collect(self) -> list[NewsItem]:
        cutoff = now_kst() - timedelta(hours=168)
        seen_urls: set[str] = set()
        items: list[NewsItem] = []

        week_ago = (now_kst() - timedelta(days=7)).strftime("%Y-%m-%d")

        for template in ML_SEARCH_QUERIES:
            query = template.format(date=week_ago)
            try:
                batch = self._search(query, cutoff)
            except Exception:
                logger.exception("[GitHub Trending] search failed for query: %s", query)
                continue

            for item in batch:
                url_key = item.url.lower()
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                items.append(item)

        items.sort(key=lambda x: x.popularity, reverse=True)
        return items[:15]

    def _search(self, query: str, cutoff) -> list[NewsItem]:
        url = f"{GITHUB_SEARCH_API}?q={quote(query)}&sort=stars&order=desc&per_page=10"
        response = requests.get(
            url,
            headers={
                **DEFAULT_HEADERS,
                "Accept": "application/vnd.github+json",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        items: list[NewsItem] = []
        for repo in payload.get("items", []):
            name = (repo.get("full_name") or "").strip()
            html_url = (repo.get("html_url") or "").strip()
            if not name or not html_url:
                continue

            description = (repo.get("description") or "").strip()
            stars = int(repo.get("stargazers_count") or 0)
            if stars > MAX_ESTABLISHED_STARS:
                continue
            topics = repo.get("topics") or []
            topic_text = ", ".join(topics[:5])
            summary_source = description or topic_text or name
            summary = summarize_text(summary_source) or name

            published_at = parse_datetime(
                repo.get("pushed_at") or repo.get("created_at")
            )
            if published_at is None:
                continue
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=KST)
            if published_at < cutoff:
                continue

            title = name
            if description:
                title = f"{name} — {description[:100]}"

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    url=html_url,
                    source=self.source_name,
                    published_at=published_at,
                    popularity=stars,
                    upvotes=stars,
                )
            )

        return items
