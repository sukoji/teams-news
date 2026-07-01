#!/usr/bin/env python3
"""Verify robots.txt allows the fetch paths used by Teams News collectors."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests

# Keep in sync with collectors.base.BOT_USER_AGENT
USER_AGENT = "PIAI-TeamsNews/1.0 (+https://sukoji.github.io/teams-news/about)"
TIMEOUT = 20


@dataclass(frozen=True)
class PathCheck:
    source: str
    base_url: str
    path: str
    robots_url: str
    optional: bool = False
    must_disallow: bool = False


CHECKS: list[PathCheck] = [
    PathCheck("GeekNews RSS", "https://news.hada.io", "/rss/news", "https://news.hada.io/robots.txt"),
    PathCheck("GeekNews RSS", "https://news.hada.io", "/rss", "https://news.hada.io/robots.txt"),
    PathCheck(
        "GeekNews topic (optional)",
        "https://news.hada.io",
        "/topic?id=1",
        "https://news.hada.io/robots.txt",
        optional=True,
    ),
    PathCheck(
        "AI Times",
        "https://cdn.aitimes.com",
        "/rss/gn_rss_allArticle.xml",
        "https://cdn.aitimes.com/robots.txt",
    ),
    PathCheck(
        "Hugging Face",
        "https://huggingface.co",
        "/api/daily_papers",
        "https://huggingface.co/robots.txt",
    ),
    PathCheck(
        "PyTorch Korea",
        "https://discuss.pytorch.kr",
        "/latest.rss",
        "https://discuss.pytorch.kr/robots.txt",
    ),
    PathCheck(
        "PyTorch Korea (must not use)",
        "https://discuss.pytorch.kr",
        "/c/news/14.rss",
        "https://discuss.pytorch.kr/robots.txt",
        must_disallow=True,
    ),
    PathCheck(
        "ETNews IT",
        "https://rss.etnews.com",
        "/Section901.xml",
        "https://rss.etnews.com/robots.txt",
    ),
    PathCheck(
        "NAVER D2",
        "https://d2.naver.com",
        "/d2.atom",
        "https://d2.naver.com/robots.txt",
    ),
    PathCheck(
        "ZDNet Korea",
        "https://feeds.feedburner.com",
        "/zdkorea",
        "https://feeds.feedburner.com/robots.txt",
    ),
    PathCheck(
        "Elvis AI Newsletter",
        "https://nlp.elvissaravia.com",
        "/feed",
        "https://nlp.elvissaravia.com/robots.txt",
    ),
]

SKIP_NOTES = [
    ("GitHub Trending", "https://api.github.com/search/repositories - Search API (robots.txt N/A)"),
]


def _looks_like_robots(text: str) -> bool:
    if not text or text.lstrip().startswith("<!"):
        return False
    lowered = text.lower()
    return "user-agent:" in lowered or "disallow:" in lowered or "allow:" in lowered


def _robots_pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """Google-style robots.txt wildcard (* = any sequence, $ = end)."""
    regex = "^"
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            regex += ".*"
        elif char == "$" and i == len(pattern) - 1:
            regex += "$"
            break
        else:
            regex += re.escape(char)
        i += 1
    if not regex.endswith("$"):
        regex += ".*"
    return re.compile(regex)


def _disallow_rules_for_star(body: str) -> list[str]:
    rules: list[str] = []
    applies = False
    for raw_line in body.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            applies = agent == "*"
            continue
        if applies and lower.startswith("disallow:"):
            rule = line.split(":", 1)[1].strip()
            if rule:
                rules.append(rule)
    return rules


def _is_disallowed(path: str, body: str) -> bool:
    for rule in _disallow_rules_for_star(body):
        if _robots_pattern_to_regex(rule).match(path):
            return True
    return False


def _load_parser(robots_url: str) -> tuple[RobotFileParser, str, str]:
    response = requests.get(
        robots_url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
    )
    parser = RobotFileParser()
    parser.parse("")

    if response.status_code == 404:
        return parser, "", "robots.txt not found (404) - all paths allowed per RFC 9309"

    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code} fetching {robots_url}")

    body = response.text
    if not _looks_like_robots(body):
        return parser, "", "no valid robots.txt body - treating as unrestricted (RSS syndication)"

    parser.parse(body.splitlines())
    return parser, body, "ok"


def _check_path(parser: RobotFileParser, base_url: str, path: str) -> bool:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    return parser.can_fetch(USER_AGENT, url)


def main() -> int:
    print(f"robots.txt compliance check (User-Agent: {USER_AGENT})\n")

    failures: list[str] = []
    cache: dict[str, tuple[RobotFileParser, str, str]] = {}

    for check in CHECKS:
        if check.robots_url not in cache:
            try:
                cache[check.robots_url] = _load_parser(check.robots_url)
            except Exception as exc:
                failures.append(f"{check.source} {check.path}: failed to fetch robots.txt - {exc}")
                continue

        parser, body, note = cache[check.robots_url]
        url = urljoin(check.base_url.rstrip("/") + "/", check.path.lstrip("/"))
        path_only = check.path.split("?", 1)[0]

        if check.must_disallow:
            blocked = _is_disallowed(path_only, body) if body else False
            allowed = not blocked
        else:
            allowed = _check_path(parser, check.base_url, check.path)

        if check.must_disallow:
            status = "PASS" if not allowed else "FAIL"
            detail = "correctly disallowed" if not allowed else "must stay disallowed"
        else:
            status = "PASS" if allowed else "FAIL"
            detail = "allowed" if allowed else "disallowed by robots.txt"

        if check.optional:
            detail += " (optional - ENABLE_GEEKNEWS_ENGAGEMENT)"

        line = f"[{status}] {check.source}: {url} - {detail} ({note})"
        print(line)

        if status == "FAIL":
            failures.append(line)

    print()
    for source, note in SKIP_NOTES:
        print(f"[SKIP] {source}: {note}")

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s)")
        return 1

    print(f"PASSED: all {len(CHECKS)} path checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
