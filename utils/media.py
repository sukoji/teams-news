from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::url)?["\']',
    re.IGNORECASE,
)


def is_valid_https_image_url(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    return True


def extract_og_image_from_html(html: str) -> str | None:
    """Return og:image or the first https image found in HTML."""
    return _first_image_from_html(html)


def _first_image_from_html(html: str) -> str | None:
    if not html or "<" not in html:
        return None

    for pattern in (_OG_IMAGE_RE, _OG_IMAGE_RE_ALT):
        match = pattern.search(html)
        if match:
            candidate = unescape(match.group(1).strip())
            if is_valid_https_image_url(candidate):
                return candidate

    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        src = (img.get("src") or img.get("data-src") or "").strip()
        if is_valid_https_image_url(src):
            return src

    return None


def extract_image_from_feed_entry(entry: Any) -> str | None:
    """Extract thumbnail/image URL from an RSS/Atom feed entry."""
    media_thumbnail = getattr(entry, "media_thumbnail", None)
    if media_thumbnail:
        url = media_thumbnail[0].get("url")
        if is_valid_https_image_url(url):
            return url

    media_content = getattr(entry, "media_content", None)
    if media_content:
        for media in media_content:
            media_type = (media.get("type") or "").lower()
            medium = (media.get("medium") or "").lower()
            if medium == "image" or media_type.startswith("image/"):
                url = media.get("url")
                if is_valid_https_image_url(url):
                    return url

    for enclosure in getattr(entry, "enclosures", None) or []:
        enc_type = (enclosure.get("type") or "").lower()
        if enc_type.startswith("image/"):
            url = enclosure.get("href") or enclosure.get("url")
            if is_valid_https_image_url(url):
                return url

    for field in ("summary", "description", "content"):
        raw = entry.get(field)
        if isinstance(raw, str):
            url = _first_image_from_html(raw)
            if url:
                return url
        elif isinstance(raw, list):
            for part in raw:
                value = part.get("value") if isinstance(part, dict) else str(part)
                url = _first_image_from_html(value)
                if url:
                    return url

    return None
