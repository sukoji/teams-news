from __future__ import annotations

from datetime import datetime

from collectors.base import NewsItem
from utils.media import is_valid_https_image_url
from utils.timezone import KST

SOURCE_COLORS: dict[str, str] = {
    "GeekNews": "Accent",
    "AI Times": "Good",
    "Hugging Face Papers": "Attention",
    "PyTorch Korea": "Warning",
}

SOURCE_ICONS: dict[str, str] = {
    "GeekNews": "📰",
    "AI Times": "📡",
    "Hugging Face Papers": "📄",
    "PyTorch Korea": "🔥",
}


def _display_title(item: NewsItem) -> str:
    return item.title_ko or item.title


def _display_summary(item: NewsItem) -> str:
    return item.summary_ko or item.summary


def _source_badge(source: str) -> dict:
    icon = SOURCE_ICONS.get(source, "📌")
    return {
        "type": "TextBlock",
        "text": f"{icon} {source}",
        "weight": "Bolder",
        "size": "Small",
        "color": SOURCE_COLORS.get(source, "Default"),
        "spacing": "None",
        "wrap": True,
    }


def _build_item_body(index: int, item: NewsItem) -> list[dict]:
    title_line = f"**{index}. {_display_title(item)}**"
    text_blocks: list[dict] = [
        {
            "type": "TextBlock",
            "text": title_line,
            "wrap": True,
            "spacing": "None",
        },
        {
            "type": "TextBlock",
            "text": _display_summary(item),
            "wrap": True,
            "spacing": "Small",
            "isSubtle": True,
            "maxLines": 3,
        },
        {
            "type": "ColumnSet",
            "spacing": "Small",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [_source_badge(item.source)],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"[원문 보기]({item.url})",
                            "horizontalAlignment": "Right",
                            "spacing": "None",
                            "wrap": True,
                        }
                    ],
                },
            ],
        },
    ]

    if is_valid_https_image_url(item.image_url):
        return [
            {
                "type": "ColumnSet",
                "spacing": "Medium",
                "columns": [
                    {
                        "type": "Column",
                        "width": "80px",
                        "items": [
                            {
                                "type": "Image",
                                "url": item.image_url,
                                "size": "Medium",
                                "style": "Default",
                                "altText": _display_title(item)[:80],
                            }
                        ],
                        "verticalContentAlignment": "Top",
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": text_blocks,
                    },
                ],
            }
        ]

    return [
        {
            "type": "Container",
            "spacing": "Medium",
            "items": text_blocks,
        }
    ]


def build_adaptive_card(items: list[NewsItem]) -> dict:
    today = datetime.now(tz=KST).strftime("%Y-%m-%d")
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

    for index, item in enumerate(items, start=1):
        body.extend(_build_item_body(index, item))
        if index < len(items):
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
