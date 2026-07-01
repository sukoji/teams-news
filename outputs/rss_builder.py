from __future__ import annotations

import logging
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

from outputs.archive import get_archive_items_by_section, get_latest_archive_items
from utils.timezone import KST

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT / "web" / "public"
FEEDS_DIR = PUBLIC_DIR / "feed"

SITE_URL = "https://sukoji.github.io/teams-news"
SITE_TITLE = "PIAI Teams News"
SITE_DESCRIPTION = (
    "Curated AI papers, tech news, trending repos, and community posts — "
    "daily digest with Korean summaries. Links to originals only."
)

SECTION_FEEDS: dict[str, str] = {
    "papers": "📄 Papers — AI research from Hugging Face Daily Papers",
    "news": "📰 News — GeekNews, AI Times, ETNews, NAVER D2, ZDNet Korea",
    "trending": "🔥 Trending — GitHub ML/AI repositories",
    "community": "💬 Community — PyTorch Korea discussions",
}


def _format_pub_date(iso_str: str) -> str:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return format_datetime(dt)


def _display_title(item: dict) -> str:
    return item.get("title_ko") or item["title"]


def _display_summary(item: dict) -> str:
    return item.get("summary_ko") or item.get("summary") or ""


def _build_item_xml(item: dict, *, extended: bool = False) -> str:
    title = escape(_display_title(item))
    link = escape(item["url"])
    description = escape(_display_summary(item))
    pub_date = _format_pub_date(item["published_at"])
    category = escape(item.get("section_id") or item.get("section", ""))
    guid = escape(item["id"])
    source = escape(item.get("source", ""))

    extra = ""
    if extended:
        engagement = item.get("engagement")
        engagement_xml = ""
        if engagement:
            engagement_xml = (
                f"<teams:engagement label=\"{escape(str(engagement.get('label', '')))}\">"
                f"{escape(str(engagement.get('value', '')))}"
                f"</teams:engagement>"
            )
        extra = f"""
      <teams:source>{source}</teams:source>
      <teams:section>{category}</teams:section>
      <teams:score>{item.get('score', 0)}</teams:score>
      <teams:titleOriginal>{escape(item.get('title', ''))}</teams:titleOriginal>
      {engagement_xml}"""

    return f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <description>{description}</description>
      <pubDate>{pub_date}</pubDate>
      <category>{category}</category>
      <source url="{link}">{source}</source>
      <guid isPermaLink="false">{guid}</guid>{extra}
    </item>"""


def build_rss_channel(
    *,
    channel_title: str,
    channel_link: str,
    channel_description: str,
    items: list[dict],
    extended: bool = False,
) -> str:
    now = format_datetime(datetime.now(tz=KST))
    xmlns = 'xmlns:teams="https://piai.postech.ac.kr/teams-news/rss/1.0"' if extended else ""
    xmlns_attr = f" {xmlns}" if extended else ""

    item_blocks = "\n".join(
        _build_item_xml(item, extended=extended) for item in items
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"{xmlns_attr}>
  <channel>
    <title>{escape(channel_title)}</title>
    <link>{escape(channel_link)}</link>
    <description>{escape(channel_description)}</description>
    <language>ko</language>
    <lastBuildDate>{now}</lastBuildDate>
    <generator>teams-news/1.0</generator>
    <docs>https://www.rssboard.org/rss-specification</docs>
{item_blocks}
  </channel>
</rss>
"""


def build_all_feeds(digest: dict, *, dry_run: bool = False) -> list[Path]:
    items: list[dict] = digest.get("items", [])
    date_str = digest.get("date", "")

    feeds: list[tuple[str | None, str, str, str, list[dict], bool]] = [
        (
            "daily.xml",
            "daily.xml",
            f"{SITE_TITLE} — Daily Top 7",
            f"{SITE_URL}/feed/daily.xml",
            "Today's curated top 7 digest for Teams card.",
            items,
            False,
        ),
        (
            "full.xml",
            "full.xml",
            f"{SITE_TITLE} — Daily Full Metadata",
            f"{SITE_URL}/feed/full.xml",
            "Extended RSS with scores, sections, and engagement metrics for bot builders.",
            items,
            True,
        ),
    ]

    written: list[Path] = []
    if dry_run:
        for _, filename, title, _, _, section_items, _ in feeds:
            logger.info("RSS dry run — %s: %d items (%s)", filename, len(section_items), title)
        return written

    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    for subdir, filename, title, link, description, section_items, extended in feeds:
        xml = build_rss_channel(
            channel_title=title,
            channel_link=link,
            channel_description=description,
            items=section_items,
            extended=extended,
        )
        if subdir is None:
            path = PUBLIC_DIR / filename
        else:
            path = FEEDS_DIR / filename
        path.write_text(xml, encoding="utf-8")
        written.append(path)
        logger.info("Wrote RSS feed: %s (%d items)", path, len(section_items))

    # data/feeds.json — avoids /feed/index.json shadowing the React /feed route on GitHub Pages
    feeds_catalog_path = PUBLIC_DIR / "data" / "feeds.json"
    feeds_catalog_path.parent.mkdir(parents=True, exist_ok=True)
    feeds_catalog_path.write_text(
        __import__("json").dumps(
            {
                "site_url": SITE_URL,
                "date": date_str,
                "feeds": {
                    "all": f"{SITE_URL}/feed.xml",
                    "daily": f"{SITE_URL}/feed/daily.xml",
                    "full": f"{SITE_URL}/feed/full.xml",
                    **{
                        sid: f"{SITE_URL}/feed/{sid}.xml"
                        for sid in SECTION_FEEDS
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    written.append(feeds_catalog_path)

    return written


ARCHIVE_FEED_LIMIT = 50


def build_archive_feeds(*, dry_run: bool = False) -> list[Path]:
    """Build main feed.xml and section feeds from the full archive."""
    archive_items = get_latest_archive_items(ARCHIVE_FEED_LIMIT)

    feeds: list[tuple[str | None, str, str, str, list[dict], bool]] = [
        (
            None,
            "feed.xml",
            f"{SITE_TITLE} — Latest from Archive",
            f"{SITE_URL}/feed",
            f"Latest {ARCHIVE_FEED_LIMIT} keyword-matched items from the growing archive.",
            archive_items,
            False,
        ),
    ]

    for section_id, section_desc in SECTION_FEEDS.items():
        section_items = get_archive_items_by_section(section_id, ARCHIVE_FEED_LIMIT)
        feeds.append(
            (
                f"{section_id}.xml",
                f"{section_id}.xml",
                f"{SITE_TITLE} — {section_desc.split(' — ')[0]}",
                f"{SITE_URL}/feed/{section_id}.xml",
                section_desc,
                section_items,
                False,
            )
        )

    written: list[Path] = []
    if dry_run:
        for _, filename, title, _, _, section_items, _ in feeds:
            logger.info("Archive RSS dry run — %s: %d items (%s)", filename, len(section_items), title)
        return written

    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    for subdir, filename, title, link, description, section_items, extended in feeds:
        xml = build_rss_channel(
            channel_title=title,
            channel_link=link,
            channel_description=description,
            items=section_items,
            extended=extended,
        )
        if subdir is None:
            path = PUBLIC_DIR / filename
        else:
            path = FEEDS_DIR / filename
        path.write_text(xml, encoding="utf-8")
        written.append(path)
        logger.info("Wrote archive RSS feed: %s (%d items)", path, len(section_items))

    return written
