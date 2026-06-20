from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from collectors.base import NewsItem
from utils.sections import SOURCE_SECTIONS
from utils.timezone import KST

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DIGESTS_DIR = ROOT / "data" / "digests"
WEB_DATA_DIR = ROOT / "web" / "public" / "data"

SECTION_IDS: dict[str, str] = {
    "📄 Papers": "papers",
    "📰 News": "news",
    "🔥 Trending": "trending",
    "💬 Community": "community",
    "📌 기타": "other",
}

DIGEST_TITLE = "📄📰 오늘의 AI 논문 & 테크 뉴스"


def _section_id(section_title: str) -> str:
    return SECTION_IDS.get(section_title, "other")


def _engagement(item: NewsItem) -> dict | None:
    if item.source == "Hugging Face Papers" and item.upvotes > 0:
        return {"label": "Upvotes", "value": item.upvotes}
    if item.source == "GitHub Trending" and item.popularity > 0:
        return {"label": "Stars", "value": item.popularity}
    if item.source == "GeekNews" and item.popularity > 0:
        return {"label": "Points", "value": item.popularity}
    return None


def _stable_guid(url: str, digest_date: str) -> str:
    raw = f"{url.strip().lower()}|{digest_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _serialize_item(item: NewsItem, digest_date: str, index: int) -> dict:
    section_title = _source_to_section().get(item.source, "📌 기타")
    return {
        "id": _stable_guid(item.url, digest_date),
        "index": index,
        "title": item.title,
        "title_ko": item.title_ko,
        "summary": item.summary,
        "summary_ko": item.summary_ko,
        "url": item.url,
        "source": item.source,
        "section": section_title,
        "section_id": _section_id(section_title),
        "published_at": item.published_at.astimezone(KST).isoformat(),
        "popularity": item.popularity,
        "upvotes": item.upvotes,
        "score": round(item.score, 2),
        "importance_score": round(item.importance_score, 2),
        "matched_keywords": item.matched_keywords,
        "engagement": _engagement(item),
    }


def _source_to_section() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for section_title, sources in SOURCE_SECTIONS:
        for source in sources:
            mapping[source] = section_title
    return mapping


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


def build_digest_payload(items: list[NewsItem], digest_date: str | None = None) -> dict:
    if digest_date is None:
        digest_date = datetime.now(tz=KST).strftime("%Y-%m-%d")

    flat: list[dict] = []
    index = 0
    for _, section_items in _group_by_section(items):
        for item in section_items:
            index += 1
            flat.append(_serialize_item(item, digest_date, index))

    sections: list[dict] = []
    for section_title, section_items in _group_by_section(items):
        section_entries = [
            entry
            for entry in flat
            if entry["section"] == section_title
        ]
        sections.append(
            {
                "id": _section_id(section_title),
                "title": section_title,
                "items": section_entries,
            }
        )

    return {
        "schema_version": 1,
        "date": digest_date,
        "generated_at": datetime.now(tz=KST).isoformat(),
        "title": DIGEST_TITLE,
        "item_count": len(flat),
        "sections": sections,
        "items": flat,
    }


def export_digest(
    items: list[NewsItem],
    *,
    digest_date: str | None = None,
    dry_run: bool = False,
) -> Path | None:
    payload = build_digest_payload(items, digest_date)
    date_str = payload["date"]

    if dry_run:
        logger.info(
            "Export dry run — would write %d items for %s",
            payload["item_count"],
            date_str,
        )
        output = json.dumps(payload, ensure_ascii=False, indent=2)
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        print(output)
        return None

    DIGESTS_DIR.mkdir(parents=True, exist_ok=True)
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    dated_path = DIGESTS_DIR / f"{date_str}.json"
    latest_path = DIGESTS_DIR / "latest.json"
    web_latest = WEB_DATA_DIR / "latest.json"

    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    dated_path.write_text(encoded, encoding="utf-8")
    latest_path.write_text(encoded, encoding="utf-8")
    web_latest.write_text(encoded, encoding="utf-8")

    web_digests = WEB_DATA_DIR / "digests"
    web_digests.mkdir(parents=True, exist_ok=True)
    (web_digests / f"{date_str}.json").write_text(encoded, encoding="utf-8")

    _update_archive_index(DIGESTS_DIR, WEB_DATA_DIR)

    logger.info("Wrote digest: %s (%d items)", dated_path, payload["item_count"])
    return dated_path


def _update_archive_index(digests_dir: Path, web_data_dir: Path) -> None:
    dates = sorted(
        p.stem for p in digests_dir.glob("*.json") if p.stem not in {"latest", "archive-index"}
    )

    date_counts: dict[str, int] = {}
    archive_meta = ROOT / "data" / "archive" / "meta.json"
    if archive_meta.exists():
        try:
            meta = json.loads(archive_meta.read_text(encoding="utf-8"))
            date_counts = meta.get("date_counts", {})
        except json.JSONDecodeError:
            pass

    digest_counts: dict[str, int] = {}
    for date in dates:
        digest_path = digests_dir / f"{date}.json"
        try:
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            digest_counts[date] = digest.get("item_count", 0)
        except (json.JSONDecodeError, OSError):
            digest_counts[date] = 0

    index = {
        "dates": list(reversed(dates)),
        "digest_counts": digest_counts,
        "archive_counts": {d: date_counts.get(d, 0) for d in dates},
    }
    encoded = json.dumps(index, ensure_ascii=False, indent=2)
    (digests_dir / "archive-index.json").write_text(encoded, encoding="utf-8")
    (web_data_dir / "archive-index.json").write_text(encoded, encoding="utf-8")
