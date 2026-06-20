#!/usr/bin/env python3
"""AI/tech news bot: collect, filter, export, RSS, archive ingest, and post to Microsoft Teams."""

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
from collectors import (
    AITimesCollector,
    ETNewsCollector,
    GeekNewsCollector,
    GitHubTrendingCollector,
    HuggingFaceCollector,
    NaverD2Collector,
    PyTorchKoreaCollector,
    ZDNetKoreaCollector,
)
from collectors.base import BaseCollector
from outputs.archive import append_items, build_search_index, sync_items_jsonl_to_web
from outputs.export import build_digest_payload, export_digest
from outputs.rss_builder import build_all_feeds, build_archive_feeds
from utils.filters import format_section_distribution, prepare_archive_items, select_top_items
from utils.translate import localize_items

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
    PyTorchKoreaCollector(),
    GitHubTrendingCollector(),
    ETNewsCollector(),
    NaverD2Collector(),
    ZDNetKoreaCollector(),
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


def run_teams(items, *, dry_run: bool) -> int:
    payload = build_teams_payload(items)

    if dry_run:
        output = json.dumps(payload, ensure_ascii=False, indent=2)
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        print(output)
        logger.info("Dry run complete — Teams payload printed, not sent.")
        return 0

    webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
    if not webhook_url:
        logger.error("TEAMS_WEBHOOK_URL environment variable is not set.")
        return 1

    try:
        send_to_teams(payload, webhook_url)
    except Exception:
        logger.exception("Failed to send message to Teams")
        return 1

    return 0


def run_export(items, *, dry_run: bool) -> int:
    digest = build_digest_payload(items)
    export_digest(items, dry_run=dry_run)
    build_all_feeds(digest, dry_run=dry_run)
    build_archive_feeds(dry_run=dry_run)
    logger.info("Export complete.")
    return 0


def run_ingest(raw_items, *, dry_run: bool, translate: bool) -> int:
    archive_candidates = prepare_archive_items(raw_items)
    if not archive_candidates:
        logger.warning("No keyword-matched items for archive.")
        return 0

    to_store = localize_items(archive_candidates) if translate else archive_candidates
    new_count = append_items(to_store, dry_run=dry_run)
    build_search_index(dry_run=dry_run)
    sync_items_jsonl_to_web(dry_run=dry_run)
    build_archive_feeds(dry_run=dry_run)
    logger.info("Ingest complete — %d new items appended.", new_count)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI/tech news Teams bot + web export")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--ingest",
        action="store_true",
        help="Append keyword-matched items to archive (no Teams/digest)",
    )
    mode.add_argument(
        "--teams",
        action="store_true",
        help="Post daily digest (top 7) to Microsoft Teams only",
    )
    mode.add_argument(
        "--export",
        action="store_true",
        help="Export daily digest JSON and RSS feeds only",
    )
    mode.add_argument(
        "--digest",
        action="store_true",
        help="Daily digest: ingest archive + export top 7 + Teams",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        help="Same as --digest (ingest + export + Teams)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect and build without writing files or Teams post",
    )
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Skip Korean translation during ingest/export",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"}
    translate = not args.no_translate

    do_ingest = args.ingest
    do_teams = args.teams or args.digest or args.all
    do_export = args.export or args.digest or args.all

    # Default when no mode flag: full daily digest flow
    if not (do_ingest or do_teams or do_export):
        do_ingest = True
        do_teams = True
        do_export = True

    logger.info("Starting news collection...")
    raw_items = collect_all()
    logger.info("Total raw items collected: %d", len(raw_items))

    if not raw_items:
        logger.warning("No news items collected from any source.")
        return 1

    exit_code = 0

    if do_ingest:
        if run_ingest(raw_items, dry_run=dry_run, translate=translate) != 0:
            exit_code = 1

    if do_teams or do_export:
        selected = select_top_items(raw_items)
        logger.info("Selected %d items for daily digest", len(selected))
        if selected:
            logger.info("Section breakdown: %s", format_section_distribution(selected))

        if not selected:
            logger.warning("No items passed filtering for digest.")
            return 1

        localized = localize_items(selected) if translate else selected
        from utils.filters import format_item_score

        for item in localized:
            logger.info(
                "  [%s] %s — %s",
                item.source,
                item.title[:80],
                format_item_score(item),
            )

        if do_export:
            if run_export(localized, dry_run=dry_run) != 0:
                exit_code = 1
        if do_teams:
            teams_code = run_teams(localized, dry_run=dry_run)
            if teams_code != 0:
                exit_code = teams_code

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
