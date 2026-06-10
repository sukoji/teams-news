from __future__ import annotations

from datetime import datetime

from collectors.base import NewsItem
from utils.timezone import KST


def build_adaptive_card(items: list[NewsItem]) -> dict:
    today = datetime.now(tz=KST).strftime("%Y-%m-%d")
    body: list[dict] = [
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
        {"type": "TextBlock", "text": " ", "separator": True, "spacing": "Medium"},
    ]

    for index, item in enumerate(items, start=1):
        body.extend(
            [
                {
                    "type": "TextBlock",
                    "text": f"{index}. {item.title}",
                    "wrap": True,
                    "weight": "Bolder",
                    "spacing": "Medium",
                },
                {
                    "type": "TextBlock",
                    "text": item.summary,
                    "wrap": True,
                    "spacing": "Small",
                },
                {
                    "type": "TextBlock",
                    "text": f"📌 출처: {item.source}",
                    "isSubtle": True,
                    "size": "Small",
                    "spacing": "Small",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": f"[원문 보기]({item.url})",
                    "spacing": "Small",
                    "wrap": True,
                },
            ]
        )

        if index < len(items):
            body.append(
                {
                    "type": "TextBlock",
                    "text": " ",
                    "separator": True,
                    "spacing": "Medium",
                }
            )

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
