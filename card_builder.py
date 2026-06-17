from __future__ import annotations

from datetime import datetime

from collectors.base import NewsItem
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

SOURCE_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("📄 Papers", ("Hugging Face Papers",)),
    (
        "📰 News",
        ("GeekNews", "AI Times", "전자신문 IT", "NAVER D2", "ZDNet Korea"),
    ),
    ("🔥 Trending", ("GitHub Trending",)),
    ("💬 Community", ("PyTorch Korea",)),
)


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


def _build_item_body(
    index: int, item: NewsItem, *, is_pick: bool = False
) -> list[dict]:
    title_prefix = "🏆 오늘의 Pick · " if is_pick else f"{index}. "
    title_size = "Medium" if is_pick else "Default"

    return [
        {
            "type": "Container",
            "style": "emphasis" if is_pick else "default",
            "spacing": "Medium",
            "items": [
                {
                    "type": "TextBlock",
                    "text": f"**{title_prefix}{_display_title(item)}**",
                    "wrap": True,
                    "spacing": "None",
                    "size": title_size,
                    "weight": "Bolder" if is_pick else "Default",
                },
                {
                    "type": "TextBlock",
                    "text": _display_summary(item),
                    "wrap": True,
                    "spacing": "Small",
                    "isSubtle": True,
                    "maxLines": 4 if is_pick else 3,
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
                    "wrap": True,
                },
            ],
        }
    ]


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
    top_item = max(items, key=lambda x: x.score) if items else None
    global_index = 0
    body: list[dict] = [
        {
            "type": "Container",
            "style": "emphasis",
            "bleed": True,
            "items": [
                {
                    "type": "TextBlock",
                    "text": "🤖 오늘의 AI/테크 연구 트렌드",
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
        },
    ]

    sections = _group_by_section(items)
    for section_index, (section_title, section_items) in enumerate(sections):
        if section_index > 0:
            body.append({"type": "TextBlock", "text": " ", "separator": True})

        body.append(
            {
                "type": "Container",
                "style": "emphasis",
                "spacing": "Medium",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": section_title,
                        "weight": "Bolder",
                        "size": "Medium",
                        "wrap": True,
                    }
                ],
            }
        )

        for item_index, item in enumerate(section_items):
            global_index += 1
            is_pick = top_item is not None and item.url == top_item.url
            body.extend(_build_item_body(global_index, item, is_pick=is_pick))
            if item_index < len(section_items) - 1:
                body.append({"type": "TextBlock", "text": " ", "separator": True})

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
