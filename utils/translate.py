from __future__ import annotations

import logging
import os
import re
from dataclasses import replace
from functools import lru_cache

from collectors.base import NewsItem

logger = logging.getLogger(__name__)

KOREAN_SOURCE = "AI Times"
KOREAN_CHAR_RE = re.compile(r"[\uac00-\ud7a3]")
LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+|(?<=[。．])\s+|(?<=[！？])\s+"
)

ENABLE_TRANSLATION = os.getenv("TRANSLATE_TO_KO", os.getenv("ENABLE_TRANSLATION", "true")).lower() in {
    "1",
    "true",
    "yes",
}
KOREAN_SUMMARY_MAX_CHARS = int(os.getenv("KOREAN_SUMMARY_MAX_CHARS", "180"))


def is_english_dominant(text: str) -> bool:
    if not text or not text.strip():
        return False

    korean = len(KOREAN_CHAR_RE.findall(text))
    latin = len(LATIN_CHAR_RE.findall(text))
    total = korean + latin
    if total == 0:
        return False
    return latin / total >= 0.55 and korean < 5


@lru_cache(maxsize=256)
def _translate_text_cached(text: str) -> str:
    from deep_translator import GoogleTranslator

    return GoogleTranslator(source="auto", target="ko").translate(text)


def translate_to_korean(text: str) -> str:
    clean = text.strip()
    if not clean or not is_english_dominant(clean):
        return text

    try:
        translated = _translate_text_cached(clean)
        return translated or text
    except Exception:
        logger.warning("Translation failed; keeping original text", exc_info=True)
        return text


def truncate_korean_summary(text: str, max_chars: int = KOREAN_SUMMARY_MAX_CHARS) -> str:
    clean = text.strip()
    if not clean:
        return ""

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(clean) if s.strip()]
    if not sentences:
        suffix = "…" if len(clean) > max_chars else ""
        return clean[:max_chars].rstrip() + suffix

    parts: list[str] = []
    total = 0
    for sentence in sentences[:3]:
        if total + len(sentence) > max_chars and parts:
            break
        parts.append(sentence)
        total += len(sentence)

    summary = " ".join(parts)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "…"
    return summary


def localize_news_item(item: NewsItem) -> NewsItem:
    if not ENABLE_TRANSLATION or item.source == KOREAN_SOURCE:
        return item

    title_ko = item.title_ko
    summary_ko = item.summary_ko

    if is_english_dominant(item.title):
        title_ko = translate_to_korean(item.title)

    if is_english_dominant(item.summary):
        summary_ko = truncate_korean_summary(translate_to_korean(item.summary))

    if title_ko == item.title_ko and summary_ko == item.summary_ko:
        return item

    return replace(item, title_ko=title_ko, summary_ko=summary_ko)


def localize_items(items: list[NewsItem]) -> list[NewsItem]:
    if not ENABLE_TRANSLATION:
        return items
    return [localize_news_item(item) for item in items]
