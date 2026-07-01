from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from collectors.base import NewsItem
from outputs.export import _serialize_item, _source_to_section, url_hash
from utils.timezone import KST

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "data" / "archive"
ITEMS_PATH = ARCHIVE_DIR / "items.jsonl"
SEARCH_INDEX_PATH = ARCHIVE_DIR / "search-index.json"
META_PATH = ARCHIVE_DIR / "meta.json"
WEB_ARCHIVE_DIR = ROOT / "web" / "public" / "data" / "archive"

SOURCE_SLUGS: dict[str, str] = {
    "GeekNews": "geeknews",
    "AI Times": "aitimes",
    "Hugging Face Papers": "huggingface",
    "PyTorch Korea": "pytorch-korea",
    "GitHub Trending": "github-trending",
    "전자신문 IT": "etnews",
    "NAVER D2": "naver-d2",
    "ZDNet Korea": "zdnet-korea",
    "Elvis AI Newsletter": "elvis-newsletter",
}

SLUG_TO_SOURCE = {slug: name for name, slug in SOURCE_SLUGS.items()}


def _archive_entry(item: NewsItem, *, collected_at: datetime) -> dict:
    section_title = _source_to_section().get(item.source, "📌 기타")
    entry = _serialize_item(item, collected_at.strftime("%Y-%m-%d"), 0)
    entry["id"] = url_hash(item.url)
    entry["source_slug"] = SOURCE_SLUGS.get(item.source, item.source.lower().replace(" ", "-"))
    entry["collected_at"] = collected_at.astimezone(KST).isoformat()
    entry.pop("index", None)
    return entry


def load_existing_ids() -> set[str]:
    if not ITEMS_PATH.exists():
        return set()
    ids: set[str] = set()
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                ids.add(record["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return ids


def load_all_entries() -> list[dict]:
    if not ITEMS_PATH.exists():
        return []
    entries: list[dict] = []
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def append_items(items: list[NewsItem], *, dry_run: bool = False) -> int:
    """Append keyword-matched items not already in archive. Returns count of new items."""
    if not items:
        return 0

    existing = load_existing_ids()
    collected_at = datetime.now(tz=KST)
    new_entries: list[dict] = []

    for item in items:
        item_id = url_hash(item.url)
        if item_id in existing:
            continue
        existing.add(item_id)
        new_entries.append(_archive_entry(item, collected_at=collected_at))

    if not new_entries:
        logger.info("Archive: no new items to append")
        return 0

    if dry_run:
        logger.info("Archive dry run — would append %d new items", len(new_entries))
        return len(new_entries)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    with ITEMS_PATH.open("a", encoding="utf-8") as handle:
        for entry in new_entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info("Archive: appended %d new items (total ids: %d)", len(new_entries), len(existing))
    return len(new_entries)


def _compact_search_entry(entry: dict) -> dict:
    title = entry.get("title_ko") or entry.get("title", "")
    summary = entry.get("summary_ko") or entry.get("summary", "")
    return {
        "id": entry["id"],
        "t": title,
        "s": summary,
        "src": entry.get("source_slug", ""),
        "sec": entry.get("section_id", ""),
        "pub": entry.get("published_at", ""),
        "col": entry.get("collected_at", ""),
        "score": entry.get("score", 0),
        "pop": entry.get("popularity", 0),
        "url": entry.get("url", ""),
        "source": entry.get("source", ""),
        "section": entry.get("section", ""),
        "title": entry.get("title", ""),
        "title_ko": entry.get("title_ko"),
        "summary": entry.get("summary", ""),
        "summary_ko": entry.get("summary_ko"),
        "engagement": entry.get("engagement"),
        "matched_keywords": entry.get("matched_keywords", []),
    }


def build_search_index(*, dry_run: bool = False) -> dict:
    entries = load_all_entries()
    entries.sort(key=lambda e: e.get("collected_at", ""), reverse=True)

    source_counts: dict[str, int] = {}
    section_counts: dict[str, int] = {}
    date_counts: dict[str, int] = {}

    for entry in entries:
        slug = entry.get("source_slug", "")
        source_counts[slug] = source_counts.get(slug, 0) + 1
        sec = entry.get("section_id", "other")
        section_counts[sec] = section_counts.get(sec, 0) + 1
        pub = entry.get("published_at", "")[:10]
        if pub:
            date_counts[pub] = date_counts.get(pub, 0) + 1

    index = {
        "schema_version": 1,
        "generated_at": datetime.now(tz=KST).isoformat(),
        "total": len(entries),
        "sources": [
            {
                "slug": slug,
                "name": SLUG_TO_SOURCE.get(slug, slug),
                "count": count,
            }
            for slug, count in sorted(source_counts.items(), key=lambda x: -x[1])
        ],
        "sections": [
            {
                "id": sec_id,
                "title": _section_title(sec_id),
                "count": count,
            }
            for sec_id, count in sorted(section_counts.items(), key=lambda x: -x[1])
        ],
        "date_counts": dict(sorted(date_counts.items(), reverse=True)),
        "items": [_compact_search_entry(e) for e in entries],
    }

    meta = {
        "schema_version": 1,
        "generated_at": index["generated_at"],
        "total": len(entries),
        "sources": index["sources"],
        "sections": index["sections"],
        "date_counts": index["date_counts"],
    }

    if dry_run:
        logger.info("Search index dry run — %d items", len(entries))
        return index

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    WEB_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    encoded_index = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    encoded_meta = json.dumps(meta, ensure_ascii=False, indent=2)

    SEARCH_INDEX_PATH.write_text(encoded_index, encoding="utf-8")
    META_PATH.write_text(encoded_meta, encoding="utf-8")
    (WEB_ARCHIVE_DIR / "search-index.json").write_text(encoded_index, encoding="utf-8")
    (WEB_ARCHIVE_DIR / "meta.json").write_text(encoded_meta, encoding="utf-8")

    logger.info("Built search index: %d items", len(entries))
    return index


def _section_title(section_id: str) -> str:
    mapping = {
        "papers": "📄 Papers",
        "news": "📰 News",
        "trending": "🔥 Trending",
        "community": "💬 Community",
        "other": "📌 기타",
    }
    return mapping.get(section_id, section_id)


def sync_items_jsonl_to_web(*, dry_run: bool = False) -> None:
    """Copy items.jsonl to web public for optional direct access."""
    if dry_run or not ITEMS_PATH.exists():
        return
    WEB_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest = WEB_ARCHIVE_DIR / "items.jsonl"
    dest.write_text(ITEMS_PATH.read_text(encoding="utf-8"), encoding="utf-8")


def get_latest_archive_items(limit: int = 50) -> list[dict]:
    entries = load_all_entries()
    entries.sort(key=lambda e: e.get("collected_at", ""), reverse=True)
    return entries[:limit]


def get_archive_items_by_section(section_id: str, limit: int = 50) -> list[dict]:
    entries = load_all_entries()
    filtered = [e for e in entries if e.get("section_id") == section_id]
    filtered.sort(key=lambda e: e.get("collected_at", ""), reverse=True)
    return filtered[:limit]
