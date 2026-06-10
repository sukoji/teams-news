#!/usr/bin/env python3
"""AI/tech news bot: collect, filter, and post to Microsoft Teams."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from card_builder import build_teams_payload
from collectors import AITimesCollector, GeekNewsCollector, HuggingFaceCollector
from collectors.base import BaseCollector
from utils.filters import select_top_items

load_dotenv(Path(__file__).resolve().parent / ".env", encoding="utf-8-sig")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

COLLECTORS: list[BaseCollector] = [
    GeekNewsCollector(),
    AITimesCollector(),
    HuggingFaceCollector(),
]


def collect_all() -> list:
    items = []
    for collector in COLLECTORS:
        items.extend(collector.safe_collect())
    return items


def send_to_teams(payload: dict, webhook_url: str) -> None:
    response = requests.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    run_id = response.headers.get("x-ms-workflow-run-id", "n/a")
    body_preview = response.text[:500] if response.text else "(empty)"
    logger.info(
        "Teams webhook response: HTTP %s, body=%s, run_id=%s",
        response.status_code,
        body_preview,
        run_id,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Teams webhook failed: HTTP {response.status_code} — {body_preview}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="AI/tech news Teams bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect and build card JSON without posting to Teams",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"}
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()

    logger.info("Starting news collection...")
    raw_items = collect_all()
    logger.info("Total raw items collected: %d", len(raw_items))

    if not raw_items:
        logger.warning("No news items collected from any source.")
        return 1

    selected = select_top_items(raw_items)
    logger.info("Selected %d items for delivery", len(selected))

    if not selected:
        logger.warning("No items passed filtering.")
        return 1

    for item in selected:
        logger.info("  [%s] %s", item.source, item.title[:80])

    payload = build_teams_payload(selected)

    if dry_run:
        output = json.dumps(payload, ensure_ascii=False, indent=2)
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        print(output)
        logger.info("Dry run complete — payload printed, not sent.")
        return 0

    if not webhook_url:
        logger.error("TEAMS_WEBHOOK_URL environment variable is not set.")
        return 1

    try:
        send_to_teams(payload, webhook_url)
    except Exception:
        logger.exception("Failed to send message to Teams")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
