from __future__ import annotations

import logging
import os
import re
from dataclasses import replace
from functools import lru_cache

import requests

from collectors.base import DEFAULT_HEADERS, NewsItem
from utils.media import extract_og_image_from_html, is_valid_https_image_url

logger = logging.getLogger(__name__)

HF_SOURCE = "Hugging Face Papers"
HF_THUMBNAIL_TEMPLATE = (
    "https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/{paper_id}.png"
)
HF_PAPER_ID_RE = re.compile(r"/papers/([^/?#]+)")

ENABLE_IMAGE_FETCH = os.getenv("ENABLE_IMAGE_FETCH", "true").lower() in {
    "1",
    "true",
    "yes",
}
IMAGE_FETCH_TIMEOUT = float(os.getenv("IMAGE_FETCH_TIMEOUT", "5"))


@lru_cache(maxsize=64)
def fetch_og_image(url: str) -> str | None:
    """Fetch og:image (or first <img>) from an article URL. Cached per run."""
    if not ENABLE_IMAGE_FETCH or not url:
        return None

    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=IMAGE_FETCH_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()
        return extract_og_image_from_html(response.text)
    except Exception:
        logger.debug("Failed to fetch image for %s", url, exc_info=True)
        return None


def hf_thumbnail_url(paper_url: str) -> str | None:
    match = HF_PAPER_ID_RE.search(paper_url)
    if not match:
        return None
    return HF_THUMBNAIL_TEMPLATE.format(paper_id=match.group(1))


def resolve_item_image(item: NewsItem) -> str | None:
    if is_valid_https_image_url(item.image_url):
        return item.image_url

    if item.source == HF_SOURCE:
        thumbnail = hf_thumbnail_url(item.url)
        return thumbnail if is_valid_https_image_url(thumbnail) else None

    return fetch_og_image(item.url)


def enrich_item_images(items: list[NewsItem]) -> list[NewsItem]:
    enriched: list[NewsItem] = []
    for item in items:
        image_url = resolve_item_image(item)
        if image_url == item.image_url:
            enriched.append(item)
        else:
            enriched.append(replace(item, image_url=image_url))
    return enriched
