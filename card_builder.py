from __future__ import annotations

from datetime import datetime

from collectors.base import NewsItem
from utils.sections import SOURCE_SECTIONS
from utils.timezone import KST

SOURCE_COLORS: dict[str, str] = {
    "GeekNews": "Accent",
    "AI Times": "Good",
    "Hugging Face Papers": "Attention",
    "PyTorch Korea": "Warning",
    "GitHub Trending": "Accent",
    "전자신문 IT": "Good",
    "NAVER D2": "Good",
    "ZDNet Korea": "Good",
}

SOURCE_ICONS: dict[str, str] = {
    "GeekNews": "📰",
    "AI Times": "📰",
    "Hugging Face Papers": "📄",
    "PyTorch Korea": "💬",
    "GitHub Trending": "🔥",
    "전자신문 IT": "📰",
    "NAVER D2": "📰",
    "ZDNet Korea": "📰",
}


def _display_title(item: NewsItem) -> str:
    return item.title_ko or item.title


def _display_summary(item: NewsItem) -> str:
    return item.summary_ko or item.summary


def _format_date(item: NewsItem) -> str:
    return item.published_at.astimezone(KST).strftime("%Y-%m-%d %H:%M")


def _engagement_fact(item: NewsItem) -> dict | None:
    if item.source == "Hugging Face Papers" and item.upvotes > 0:
        return {"title": "Upvotes", "value": str(item.upvotes)}
    if item.source == "GitHub Trending" and item.popularity > 0:
        return {"title": "Stars", "value": f"{item.popularity:,}"}
    if item.source == "GeekNews" and item.popularity > 0:
        return {"title": "Points", "value": str(item.popularity)}
    return None


def _item_facts(item: NewsItem) -> list[dict]:
    icon = SOURCE_ICONS.get(item.source, "📌")
    facts: list[dict] = [
        {"title": "출처", "value": f"{icon} {item.source}"},
        {"title": "날짜", "value": _format_date(item)},
    ]
    engagement = _engagement_fact(item)
    if engagement:
        facts.append(engagement)
    return facts


def _build_item_container(index: int, item: NewsItem) -> dict:
    return {
        "type": "Container",
        "spacing": "Small",
        "items": [
            {
                "type": "TextBlock",
                "text": f"**{index}. {_display_title(item)}**",
                "wrap": True,
                "spacing": "None",
                "weight": "Bolder",
                "maxLines": 2,
            },
            {
                "type": "TextBlock",
                "text": _display_summary(item),
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True,
                "size": "Small",
                "maxLines": 2,
            },
            {
                "type": "FactSet",
                "spacing": "Small",
                "facts": _item_facts(item),
            },
            {
                "type": "TextBlock",
                "text": f"[원문 보기]({item.url})",
                "spacing": "Small",
                "size": "Small",
                "wrap": True,
            },
        ],
    }


def _build_item_column(index: int, item: NewsItem) -> dict:
    return {
        "type": "Column",
        "width": "stretch",
        "items": [_build_item_container(index, item)],
    }


def _build_paired_rows(indexed_items: list[tuple[int, NewsItem]]) -> list[dict]:
    rows: list[dict] = []
    i = 0
    while i < len(indexed_items):
        idx1, item1 = indexed_items[i]
        if i + 1 < len(indexed_items):
            idx2, item2 = indexed_items[i + 1]
            rows.append(
                {
                    "type": "ColumnSet",
                    "spacing": "Small",
                    "bleed": True,
                    "columns": [
                        _build_item_column(idx1, item1),
                        _build_item_column(idx2, item2),
                    ],
                }
            )
            i += 2
        else:
            rows.append(
                {
                    "type": "ColumnSet",
                    "spacing": "Small",
                    "bleed": True,
                    "columns": [_build_item_column(idx1, item1)],
                }
            )
            i += 1
    return rows


def _group_by_section(items: list[NewsItem]) -> list[tuple[str, list[NewsItem]]]:
    by_source: dict[str, list[NewsItem]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)

    grouped: list[tuple[str, list[NewsItem]]] = []
    seen_sources: set[str] = set()

    for section_title, sources in SOURCE_SECTIONS:
        section_items: list[NewsItem] = []
        for source in sources:
            section_items.extend(by_source.get(source, []))
            seen_sources.add(source)
        if section_items:
            grouped.append((section_title, section_items))

    other_items: list[NewsItem] = []
    for source, source_items in by_source.items():
        if source not in seen_sources:
            other_items.extend(source_items)
    if other_items:
        grouped.append(("📌 기타", other_items))

    return grouped


def build_adaptive_card(items: list[NewsItem]) -> dict:
    today = datetime.now(tz=KST).strftime("%Y-%m-%d")
    global_index = 0
    header: dict = {
        "type": "Container",
        "style": "emphasis",
        "bleed": True,
        "items": [
            {
                "type": "TextBlock",
                "text": "📄📰 오늘의 AI 논문 & 테크 뉴스",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": f"📅 {today} · 상위 {len(items)}건",
                "isSubtle": True,
                "spacing": "None",
                "wrap": True,
            },
        ],
    }

    content_items: list[dict] = []
    sections = _group_by_section(items)
    for section_index, (section_title, section_items) in enumerate(sections):
        if section_index > 0:
            content_items.append({"type": "TextBlock", "text": " ", "separator": True})

        section_blocks: list[dict] = [
            {
                "type": "TextBlock",
                "text": section_title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            }
        ]

        indexed_section: list[tuple[int, NewsItem]] = []
        for item in section_items:
            global_index += 1
            indexed_section.append((global_index, item))

        paired_rows = _build_paired_rows(indexed_section)
        for row_index, row in enumerate(paired_rows):
            section_blocks.append(row)
            if row_index < len(paired_rows) - 1:
                section_blocks.append({"type": "TextBlock", "text": " ", "separator": True})

        content_items.append(
            {
                "type": "Container",
                "style": "emphasis",
                "bleed": True,
                "spacing": "Small",
                "items": section_blocks,
            }
        )

    body: list[dict] = [
        header,
        {
            "type": "Container",
            "bleed": True,
            "spacing": "Small",
            "items": content_items,
        },
    ]

    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
        "msteams": {"width": "Full"},
    }
    return card


def build_teams_payload(items: list[NewsItem]) -> dict:
    card = build_adaptive_card(items)
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": card,
            }
        ],
    }
