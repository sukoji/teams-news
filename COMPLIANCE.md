# 수집 준수 현황 (Collection Compliance)

Teams 웹훅·워크플로 변경 전 참고용 요약입니다.  
상세 경로·CI 검증은 [README — robots.txt 준수](README.md#robotstxt-준수) 및 `scripts/check_robots.py`를 참고하세요.

## 수집 방식

| 항목 | 상태 |
|------|------|
| 전체 기사 HTML 스크래핑 | **하지 않음** — RSS/Atom/JSON API만 사용 |
| 본문 전문 저장·전송 | **하지 않음** — 제목·요약·원문 URL만 |
| og:image / 썸네일 스크래핑 | **기본 비활성** (`ENABLE_IMAGE_FETCH=false`) |
| 식별 가능 User-Agent | `PIAI-TeamsNews/1.0 (+https://sukoji.github.io/teams-news/about)` |
| robots.txt CI 검증 | PR/push 시 [Collection Compliance](.github/workflows/compliance.yml) 워크플로 |

## 소스별 robots.txt (2026-06-25 확인)

| 소스 | robots.txt | 봇이 사용하는 경로 | 비고 |
|------|------------|-------------------|------|
| GeekNews | `Allow: /` (`User-agent: *`) | `/rss/news`, `/rss` | 토픽 HTML(`/topic?id=`)는 **기본 비활성** (`ENABLE_GEEKNEWS_ENGAGEMENT=false`) |
| AI Times | `Disallow: /admin/` only | `cdn.aitimes.com/rss/*.xml` | |
| Hugging Face | `Allow: /` | `/api/daily_papers` | |
| PyTorch Korea | `Disallow: /c/*.rss` | `/latest.rss` + 카테고리 필터 | `/c/news/14.rss` **미사용** |
| GitHub Trending | N/A (Search API) | `/search/repositories` | robots.txt 대상 아님 |
| 전자신문 IT | `Allow: /` | `rss.etnews.com/Section901.xml` | |
| NAVER D2 | **404** (파일 없음) | `d2.naver.com/d2.atom` | RFC 9309상 전 경로 허용 |
| ZDNet Korea | 유효한 robots.txt 없음 | `feeds.feedburner.com/zdkorea` | FeedBurner RSS 공개 피드 |

## 웹훅 변경 시 체크리스트

1. **수집 로직·스케줄은 변경하지 않아도 됩니다** — Teams 전송만 웹훅 URL에 의존합니다.
2. GitHub **Settings → Secrets → Actions**에서 `TEAMS_WEBHOOK_URL`만 새 Workflows 웹훅 URL로 갱신하세요.
3. `cron.yml` 스케줄·수집 소스는 그대로 두고, 필요 시 Actions에서 **Run workflow**로 digest를 수동 실행해 확인하세요.
4. GeekNews 토픽 페이지 HTML 수집을 켜려면 `ENABLE_GEEKNEWS_ENGAGEMENT=true`로 명시 설정하세요 (기본 `false`).

## 자동 검증

```bash
python scripts/check_robots.py
```

모든 필수 경로가 허용되고, PyTorch `/c/news/14.rss`는 거부되는지 확인합니다.
