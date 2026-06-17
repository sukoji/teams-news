from __future__ import annotations

import logging
import math
import os
import re
from html import unescape

from bs4 import BeautifulSoup

from collectors.base import NewsItem
from utils.timezone import now_kst

logger = logging.getLogger(__name__)

KEYWORDS: tuple[str, ...] = (
    "ai",
    "llm",
    "agent",
    "rag",
    "deep learning",
    "transformer",
    "오피소스",
    "open source",
    "opensource",
    "gpt",
    "claude",
    "gemini",
    "huggingface",
    "machine learning",
    "추론",
    "연구",
    "fine-tuning",
    "fine tuning",
    "finetuning",
    "multimodal",
    "diffusion",
    "embedding",
    "vector",
    "neural",
    "reinforcement learning",
    "rlhf",
    "mcp",
    "reasoning",
    "vision language",
    "vlm",
    "benchmark",
    "paper",
    "모델",
    "foundation model",
    "inference",
    "training",
    "dataset",
    "open-weight",
    "open weight",
)

HF_SOURCE = "Hugging Face Papers"
GEEKNEWS_SOURCE = "GeekNews"
AITIMES_SOURCE = "AI Times"
PYTORCH_KOREA_SOURCE = "PyTorch Korea"
GITHUB_TRENDING_SOURCE = "GitHub Trending"
ETNEWS_SOURCE = "전자신문 IT"
NAVER_D2_SOURCE = "NAVER D2"
ZDNET_KOREA_SOURCE = "ZDNet Korea"
ALL_SOURCES: tuple[str, ...] = (
    HF_SOURCE,
    GITHUB_TRENDING_SOURCE,
    GEEKNEWS_SOURCE,
    AITIMES_SOURCE,
    ETNEWS_SOURCE,
    NAVER_D2_SOURCE,
    ZDNET_KOREA_SOURCE,
    PYTORCH_KOREA_SOURCE,
)

MIN_ITEMS = int(os.getenv("MIN_ITEMS", "5"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "7"))
MIN_PER_SOURCE = int(os.getenv("MIN_PER_SOURCE", "1"))
MAX_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE", "3"))
IMPORTANCE_WEIGHT = float(os.getenv("IMPORTANCE_WEIGHT", "1.0"))
RECENCY_WEIGHT = float(os.getenv("RECENCY_WEIGHT", "0.5"))
RECENCY_WINDOW_HOURS = float(os.getenv("RECENCY_WINDOW_HOURS", "24"))
MIN_UPVOTES = int(os.getenv("MIN_UPVOTES", "0"))


def strip_html(text: str) -> str:
    if not text:
        return ""
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def summarize_text(text: str, max_chars: int = 220) -> str:
    clean = strip_html(text)
    if not clean:
        return ""

    sentences = re.split(
        r"(?<=[.!?])\s+|(?<=[。．])\s+|(?<=[！？!?])\s+",
        clean,
    )
    summary_parts: list[str] = []
    total = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if total + len(sentence) > max_chars and summary_parts:
            break
        summary_parts.append(sentence)
        total += len(sentence)
        if len(summary_parts) >= 3:
            break

    if not summary_parts:
        suffix = "…" if len(clean) > max_chars else ""
        return clean[:max_chars].rstrip() + suffix

    summary = " ".join(summary_parts)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "…"
    return summary


def _keyword_hits(text: str) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    for keyword in KEYWORDS:
        if keyword.lower() in lowered:
            hits.append(keyword)
    return hits


def _keyword_score(item: NewsItem, hits: list[str]) -> float:
    if item.source == HF_SOURCE:
        return 4.0 + len(hits) * 2.0

    score = len(hits) * 3.0
    if hits:
        score += 2.0
    return score


def _popularity_score(item: NewsItem) -> float:
    popularity = max(item.popularity, 0)
    if popularity == 0:
        return 0.0

    if item.source == HF_SOURCE:
        return min(math.log1p(popularity), 6.0) * 3.0
    if item.source == GEEKNEWS_SOURCE:
        return min(math.log1p(popularity), 5.0) * 4.0
    if item.source == AITIMES_SOURCE:
        return popularity / 10.0
    if item.source == PYTORCH_KOREA_SOURCE:
        return popularity / 10.0
    if item.source == GITHUB_TRENDING_SOURCE:
        return min(math.log1p(popularity), 7.0) * 3.5
    if item.source in {ETNEWS_SOURCE, NAVER_D2_SOURCE, ZDNET_KOREA_SOURCE}:
        return popularity / 10.0
    return min(math.log1p(popularity), 5.0)


def _recency_score(item: NewsItem, now) -> float:
    age_hours = (now - item.published_at).total_seconds() / 3600.0
    if age_hours < 0:
        age_hours = 0.0
    if age_hours >= RECENCY_WINDOW_HOURS:
        return 0.0
    return (RECENCY_WINDOW_HOURS - age_hours) / RECENCY_WINDOW_HOURS * 10.0


def score_item(item: NewsItem) -> NewsItem:
    searchable = f"{item.title} {item.summary}"
    hits = _keyword_hits(searchable)

    if item.source == HF_SOURCE:
        item.matched_keywords = hits or ["AI research"]
    else:
        item.matched_keywords = hits

    keyword = _keyword_score(item, hits)
    popularity = _popularity_score(item)
    recency = _recency_score(item, now_kst())

    if item.source == HF_SOURCE and MIN_UPVOTES > 0 and item.upvotes < MIN_UPVOTES:
        popularity *= 0.5

    item.importance_score = popularity + recency
    item.score = keyword + IMPORTANCE_WEIGHT * popularity + RECENCY_WEIGHT * recency
    return item


def passes_keyword_filter(item: NewsItem) -> bool:
    if item.source == HF_SOURCE:
        return True
    return bool(item.matched_keywords)


def deduplicate_items(items: list[NewsItem]) -> list[NewsItem]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[NewsItem] = []

    for item in sorted(items, key=lambda x: x.published_at, reverse=True):
        url_key = item.url.split("?")[0].rstrip("/").lower()
        title_key = re.sub(r"\s+", " ", item.title.lower()).strip()

        if url_key in seen_urls or title_key in seen_titles:
            continue

        seen_urls.add(url_key)
        seen_titles.add(title_key)
        unique.append(item)

    return unique


def _group_by_source(ranked: list[NewsItem]) -> dict[str, list[NewsItem]]:
    grouped: dict[str, list[NewsItem]] = {source: [] for source in ALL_SOURCES}
    for item in ranked:
        grouped.setdefault(item.source, []).append(item)
    return grouped


def _select_balanced(ranked: list[NewsItem], max_items: int) -> list[NewsItem]:
    """Ensure each source contributes when available, then fill by score."""
    by_source = _group_by_source(ranked)
    selected: list[NewsItem] = []
    seen_urls: set[str] = set()
    source_counts: dict[str, int] = {source: 0 for source in ALL_SOURCES}

    def try_add(item: NewsItem) -> bool:
        if item.url in seen_urls:
            return False
        if source_counts.get(item.source, 0) >= MAX_PER_SOURCE:
            return False
        seen_urls.add(item.url)
        selected.append(item)
        source_counts[item.source] = source_counts.get(item.source, 0) + 1
        return True

    # Phase 1: at least MIN_PER_SOURCE from each source (when available).
    for _ in range(MIN_PER_SOURCE):
        if len(selected) >= max_items:
            break
        for source in ALL_SOURCES:
            if len(selected) >= max_items:
                break
            pool = by_source.get(source, [])
            index = source_counts.get(source, 0)
            if index < len(pool):
                try_add(pool[index])

    # Phase 2: fill remaining slots by global rank, respecting per-source cap.
    for item in ranked:
        if len(selected) >= max_items:
            break
        try_add(item)

    selected.sort(
        key=lambda item: (item.score, item.importance_score, item.published_at),
        reverse=True,
    )
    return selected[:max_items]


def format_item_score(item: NewsItem) -> str:
    return (
        f"score={item.score:.1f} "
        f"(kw={_keyword_score(item, item.matched_keywords):.1f}, "
        f"pop={item.popularity}, imp={item.importance_score:.1f})"
    )


def select_top_items(items: list[NewsItem]) -> list[NewsItem]:
    scored = [score_item(item) for item in items]
    filtered = [item for item in scored if passes_keyword_filter(item)]
    filtered = deduplicate_items(filtered)

    ranked = sorted(
        filtered,
        key=lambda item: (item.score, item.importance_score, item.published_at),
        reverse=True,
    )

    if ranked:
        for index, item in enumerate(ranked[:10], start=1):
            logger.debug(
                "Rank %d [%s] %s — %s",
                index,
                item.source,
                item.title[:60],
                format_item_score(item),
            )

        balanced = _select_balanced(ranked, MAX_ITEMS)
        if len(balanced) >= MIN_ITEMS:
            for item in balanced:
                logger.info(
                    "Selected [%s] %s — %s",
                    item.source,
                    item.title[:80],
                    format_item_score(item),
                )
            return balanced

    fallback = deduplicate_items(scored)
    fallback = sorted(fallback, key=lambda item: item.published_at, reverse=True)
    merged: list[NewsItem] = []
    seen: set[str] = set()

    for item in ranked + fallback:
        if item.url in seen:
            continue
        seen.add(item.url)
        merged.append(item)
        if len(merged) >= MAX_ITEMS:
            break

    return merged
