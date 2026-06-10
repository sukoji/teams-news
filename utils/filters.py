from __future__ import annotations

import os
import re
from html import unescape

from bs4 import BeautifulSoup

from collectors.base import NewsItem

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
ALL_SOURCES: tuple[str, ...] = (GEEKNEWS_SOURCE, AITIMES_SOURCE, HF_SOURCE)

MIN_ITEMS = int(os.getenv("MIN_ITEMS", "5"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "7"))
MIN_PER_SOURCE = int(os.getenv("MIN_PER_SOURCE", "1"))
MAX_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE", "3"))


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


def score_item(item: NewsItem) -> NewsItem:
    searchable = f"{item.title} {item.summary}"
    hits = _keyword_hits(searchable)

    if item.source == HF_SOURCE:
        item.matched_keywords = hits or ["AI research"]
        item.score = 4 + len(hits) * 2
        return item

    item.matched_keywords = hits
    item.score = len(hits) * 3
    if hits:
        item.score += 2
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

    selected.sort(key=lambda item: (item.score, item.published_at), reverse=True)
    return selected[:max_items]


def select_top_items(items: list[NewsItem]) -> list[NewsItem]:
    scored = [score_item(item) for item in items]
    filtered = [item for item in scored if passes_keyword_filter(item)]
    filtered = deduplicate_items(filtered)

    ranked = sorted(
        filtered,
        key=lambda item: (item.score, item.published_at),
        reverse=True,
    )

    if ranked:
        balanced = _select_balanced(ranked, MAX_ITEMS)
        if len(balanced) >= MIN_ITEMS:
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
