from __future__ import annotations

import logging
import math
import os
import re
from html import unescape

from bs4 import BeautifulSoup

from collectors.base import NewsItem
from utils.sections import SOURCE_SECTIONS
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
MAX_PER_SECTION = int(os.getenv("MAX_PER_SECTION", "0"))
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


def _source_to_section() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for section_title, sources in SOURCE_SECTIONS:
        for source in sources:
            mapping[source] = section_title
    return mapping


def _section_labels() -> list[str]:
    return [title for title, _ in SOURCE_SECTIONS]


def _parse_section_targets(max_items: int) -> dict[str, int]:
    section_titles = _section_labels()
    raw = os.getenv("SECTION_TARGETS", "").strip()
    if raw:
        parts = [int(part.strip()) for part in raw.split(",")]
        if len(parts) != len(section_titles):
            raise ValueError(
                f"SECTION_TARGETS must have {len(section_titles)} values "
                f"for {section_titles}, got {len(parts)}"
            )
        total = sum(parts)
        if total != max_items:
            logger.warning(
                "SECTION_TARGETS sum (%d) != MAX_ITEMS (%d); using targets as-is",
                total,
                max_items,
            )
        return dict(zip(section_titles, parts))

    base, remainder = divmod(max_items, len(section_titles))
    return {
        title: base + (1 if index < remainder else 0)
        for index, title in enumerate(section_titles)
    }


def _group_by_section(ranked: list[NewsItem]) -> dict[str, list[NewsItem]]:
    source_to_section = _source_to_section()
    grouped: dict[str, list[NewsItem]] = {title: [] for title, _ in SOURCE_SECTIONS}
    for item in ranked:
        section = source_to_section.get(item.source)
        if section:
            grouped[section].append(item)
    return grouped


def section_distribution(items: list[NewsItem]) -> dict[str, int]:
    source_to_section = _source_to_section()
    counts: dict[str, int] = {title: 0 for title, _ in SOURCE_SECTIONS}
    for item in items:
        section = source_to_section.get(item.source)
        if section:
            counts[section] += 1
    return counts


def format_section_distribution(items: list[NewsItem]) -> str:
    counts = section_distribution(items)
    parts = [f"{title} {counts[title]}" for title in counts]
    return ", ".join(parts)


def _select_section_balanced(ranked: list[NewsItem], max_items: int) -> list[NewsItem]:
    """Pick roughly equal items per card section, then fill leftover slots by score."""
    source_to_section = _source_to_section()
    section_targets = _parse_section_targets(max_items)
    max_per_section = MAX_PER_SECTION or max(section_targets.values())

    by_section = _group_by_section(ranked)
    selected: list[NewsItem] = []
    seen_urls: set[str] = set()
    source_counts: dict[str, int] = {source: 0 for source in ALL_SOURCES}
    section_counts: dict[str, int] = {title: 0 for title, _ in SOURCE_SECTIONS}

    def can_add(item: NewsItem, *, enforce_section_target: bool) -> bool:
        if item.url in seen_urls:
            return False
        if source_counts.get(item.source, 0) >= MAX_PER_SOURCE:
            return False
        section = source_to_section.get(item.source)
        if not section:
            return False
        if section_counts.get(section, 0) >= max_per_section:
            return False
        if (
            enforce_section_target
            and section_counts.get(section, 0) >= section_targets.get(section, 0)
        ):
            return False
        return True

    def try_add(item: NewsItem, *, enforce_section_target: bool) -> bool:
        if not can_add(item, enforce_section_target=enforce_section_target):
            return False
        seen_urls.add(item.url)
        selected.append(item)
        source_counts[item.source] = source_counts.get(item.source, 0) + 1
        section = source_to_section[item.source]
        section_counts[section] = section_counts.get(section, 0) + 1
        return True

    # Phase 1: fill each section toward its target with highest-scored items.
    for section_title, _ in SOURCE_SECTIONS:
        target = section_targets[section_title]
        for item in by_section[section_title]:
            if section_counts[section_title] >= target:
                break
            try_add(item, enforce_section_target=True)

    # Phase 2: redistribute unfilled slots to sections still below target.
    for item in ranked:
        if len(selected) >= max_items:
            break
        try_add(item, enforce_section_target=True)

    # Phase 3: if some sections had no content, fill remaining slots by score.
    for item in ranked:
        if len(selected) >= max_items:
            break
        try_add(item, enforce_section_target=False)

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


def prepare_archive_items(items: list[NewsItem]) -> list[NewsItem]:
    """Score, keyword-filter, and dedupe all matching items (not capped at top 7)."""
    scored = [score_item(item) for item in items]
    filtered = [item for item in scored if passes_keyword_filter(item)]
    ranked = sorted(
        deduplicate_items(filtered),
        key=lambda item: (item.score, item.importance_score, item.published_at),
        reverse=True,
    )
    logger.info("Archive candidates: %d keyword-matched items", len(ranked))
    return ranked


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

        balanced = _select_section_balanced(ranked, MAX_ITEMS)
        if len(balanced) >= MIN_ITEMS:
            logger.info(
                "Section distribution: %s",
                format_section_distribution(balanced),
            )
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
