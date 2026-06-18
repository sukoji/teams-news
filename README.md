# Teams AI / Tech News Bot

AI 연구원·개발자를 위한 **AI/테크 뉴스 자동 수집 봇**입니다.  
GeekNews, AI Times, Hugging Face Daily Papers, PyTorch Korea, **GitHub Trending**, **전자신문 IT**, **NAVER D2**, **ZDNet Korea**에서 최근 24시간(NAVER D2·GitHub Trending은 7일) 이내 기사·레포를 수집하고, 키워드 필터링 후 Microsoft Teams 채널에 **Adaptive Card**로 발행합니다.

## 저장소 구조

```
teams_news/
├── main.py                      # 진입점: 수집 → 필터 → 번역 → Teams 전송
├── card_builder.py              # Adaptive Card JSON 생성 (섹션·FactSet 레이아웃)
├── assets/piai-logo.png         # PIAI 로고 (카드 썸네일 기본값)
├── requirements.txt
├── .env.example
├── .github/workflows/cron.yml   # GitHub Actions 스케줄 (매일 ~10:00 KST)
├── collectors/
│   ├── base.py                  # NewsItem, BaseCollector
│   ├── geeknews.py              # GeekNews RSS
│   ├── aitimes.py               # AI Times RSS
│   ├── huggingface.py           # HF Daily Papers API
│   ├── pytorch_korea.py         # PyTorch Korea 읽을거리&정보공유 RSS
│   ├── github_trending.py       # GitHub Search API (ML/AI 신규 레포)
│   ├── etnews.py                # 전자신문 IT RSS
│   ├── naver_d2.py              # NAVER D2 Atom
│   └── zdnet_korea.py           # ZDNet Korea RSS
└── utils/
    ├── filters.py               # 24h·키워드 필터, 소스 균형 선별
    ├── translate.py             # 영문 → 한국어 요약 (deep-translator)
    ├── thumbnail.py             # PIAI 카드 썸네일 URL
    ├── image_fetch.py           # (비활성) og:image 스크래핑 — ENABLE_IMAGE_FETCH=false
    ├── media.py                 # HTTPS 이미지 URL 검증
    └── timezone.py              # KST 타임존
```

## 데이터 소스

| 소스 | URL | 방식 |
|------|-----|------|
| GeekNews | `https://news.hada.io/rss/news` | RSS (403 시 `/rss` 폴백) |
| AI Times | `https://cdn.aitimes.com/rss/gn_rss_allArticle.xml` | RSS |
| Hugging Face Papers | `https://huggingface.co/api/daily_papers` | JSON API |
| PyTorch Korea | `https://discuss.pytorch.kr/c/news/14` (읽을거리&정보공유) | Discourse `/latest.rss` + 카테고리 필터 (robots.txt 준수) |
| GitHub Trending | `https://api.github.com/search/repositories` | Search API (topic: ML/LLM/PyTorch, 최근 7일 생성) |
| 전자신문 IT | `https://rss.etnews.com/Section901.xml` | RSS |
| NAVER D2 | `https://d2.naver.com/d2.atom` | Atom |
| ZDNet Korea | `https://feeds.feedburner.com/zdkorea` | RSS |

### robots.txt 준수

각 소스의 `robots.txt`를 확인하고, 허용된 경로·방식만 사용합니다.

| 소스 | robots.txt | 허용 경로 (봇이 사용) | 비허용·조정 |
|------|------------|----------------------|-------------|
| **GeekNews** (`news.hada.io`) | `User-agent: *` → `Allow: /` | `/rss/news`, `/rss` (RSS), `/topic?id=` (인기도) | `/api/`, `/auth/`, `/login` 등 — 미사용 |
| **AI Times** (`aitimes.com`, `cdn.aitimes.com`) | `Disallow: /admin/` only | `cdn.aitimes.com/rss/*.xml` (RSS) | 기사 HTML·og:image 스크래핑 — **비활성** |
| **Hugging Face** (`huggingface.co`) | `Allow: /` | `/api/daily_papers` (JSON API) | 논문 썸네일 CDN — **카드에 미사용** |
| **PyTorch Korea** (`discuss.pytorch.kr`) | `Disallow: /c/*.rss`, `/t/*/*.rss` | `/latest.rss` (사이트 전체 최신 RSS) | `/c/news/14.rss` — **robots.txt 위반** → `/latest.rss`에서 `읽을거리&정보공유` 카테고리만 필터 |
| **GitHub Trending** (`api.github.com`) | Search API 허용 | `/search/repositories` (인증 없이 일 1회 수준) | `github.com/trending` HTML 스크래핑·Heroku API — **미사용** |
| **전자신문** (`rss.etnews.com`) | RSS 제공 | `rss.etnews.com/Section901.xml` | 기사 HTML 스크래핑 — **미사용** |
| **NAVER D2** (`d2.naver.com`) | `Allow: /` | `/d2.atom` (Atom) | — |
| **ZDNet Korea** (`feeds.feedburner.com`) | FeedBurner RSS | `feeds.feedburner.com/zdkorea` | — |

> **썸네일**: 기사별 썸네일·og:image 수집·표시를 사용하지 않습니다 (`ENABLE_IMAGE_FETCH=false` 기본). 카드는 텍스트·FactSet 중심 레이아웃입니다.

### 수집·필터 기준

- **시간**: 최근 24시간 이내 게시물 (HF Papers 48h, NAVER D2·GitHub Trending 7일 완화)
- **키워드**: AI, LLM, Agent, RAG, Deep Learning, Transformer, 오픈소스 등
- **선별**: 키워드 점수 + **인기도/중요도** + **최신성** 가중 합산 후, **소스별 최소 1건** 보장하여 상위 **5~7건** (기본 7건, 소스당 최대 3건)

### 인기도 신호 (소스별)

| 소스 | 신호 | 비고 |
|------|------|------|
| GeekNews | 토픽 **추천(P)** + **댓글 수** | RSS에 없어 토픽 페이지에서 수집 (`ENABLE_GEEKNEWS_ENGAGEMENT`) |
| AI Times | RSS **노출 순서** | 앞쪽 기사일수록 높은 점수 (조회수 필드 없음) |
| Hugging Face | **upvotes**, **댓글**, **GitHub stars** | Daily Papers API 필드 활용 |
| PyTorch Korea | RSS **노출 순서** | 앞쪽 게시물일수록 높은 점수 (좋아요·댓글은 RSS 미제공) |
| GitHub Trending | **GitHub stars** | Search API `stargazers_count`, 5,000 stars 초과 mega-repo 제외 |
| 전자신문 IT / NAVER D2 / ZDNet Korea | RSS **노출 순서** | 앞쪽 기사일수록 높은 점수 |

최종 점수 = 키워드 관련도 + `IMPORTANCE_WEIGHT` × 인기도 + `RECENCY_WEIGHT` × 최신성(24h 이내). 소스 균형 선별 시 각 소스에서 **가장 높은 점수** 항목을 우선 선택합니다.

## 스케줄 (GitHub Actions)

봇은 **GitHub Actions cron**으로 주기적으로 실행됩니다. 별도 서버나 상시 실행 프로세스는 필요 없습니다.

| 항목 | 값 |
|------|-----|
| 기본 도착 시각 | **매일 ~10:00 KST** (UTC `0 23 * * *`, GitHub 지연 ~2h 보정) |
| 워크플로 파일 | `.github/workflows/cron.yml` |
| 수동 실행 | Actions 탭 → **Daily AI Tech News Bot** → **Run workflow** |

> **GitHub Actions 지연**: cron은 UTC 기준이며, 실제 실행은 **수 시간 늦게** 시작되는 경우가 많습니다.  
> 예) `17 20 * * *` → 실제 도착 ~07:15 KST. 현재 `0 23 * * *` → **~10:00 KST** 목표.

### 스케줄 커스터마이즈

`cron.yml`의 `schedule` 블록을 수정합니다. GitHub Actions cron은 **UTC** 기준입니다.

```yaml
on:
  schedule:
    # ~10:00 KST 도착 목표 (GitHub 지연 보정)
    - cron: "0 23 * * *"
    # 18:00 KST = 09:00 UTC — 저녁 digest 추가 시 주석 해제
    # - cron: "0 9 * * *"
```

**KST → UTC 변환**: KST = UTC + 9시간. 예) 18:00 KST → 09:00 UTC → `0 9 * * *`

> **참고**: GitHub Actions 스케줄은 **수 분~수 시간** 지연될 수 있습니다. 정확한 시각이 중요하면 Actions → **Run workflow**를 외부 cron(cron-job.org 등)으로 호출하거나, 자체 서버 cron + `python main.py`를 사용하세요.

## Microsoft Teams 웹훅 설정

### 1. Workflows에서 Incoming Webhook 생성

1. Teams에서 뉴스를 받을 **팀·채널**을 엽니다.
2. 채널 상단 **⋯ (더 보기)** → **Workflows** 를 선택합니다.
3. **Send webhook alerts to a channel** (또는 유사한 "채널에 웹훅으로 메시지 보내기") 템플릿을 선택합니다.
4. 워크플로 이름을 지정하고, 대상 **팀·채널**을 선택합니다.
5. 생성이 완료되면 **Webhook URL** 이 표시됩니다. 이 URL을 복사해 둡니다.

> **참고**: 구 Office 365 Connector는 단계적 폐지 중입니다. 신규 설정은 **Teams Workflows** 웹훅을 사용하세요.

### 2. GitHub Secret 등록

1. GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. Name: `TEAMS_WEBHOOK_URL`
4. Value: 1단계에서 복사한 웹훅 URL
5. **Add secret** 저장

## 환경 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `TEAMS_WEBHOOK_URL` | ✅ | — | Teams Workflows 웹훅 URL |
| `DRY_RUN` | | `false` | `true`면 Teams 전송 없이 JSON 출력 |
| `MAX_ITEMS` | | `7` | 카드에 포함할 최대 기사 수 |
| `MIN_ITEMS` | | `5` | 키워드 필터 후 목표 최소 기사 수 |
| `MIN_PER_SOURCE` | | `1` | 소스별 최소 포함 건수 (8개 소스 균형) |
| `MAX_PER_SOURCE` | | `3` | 소스별 최대 포함 건수 (HF 독점 방지) |
| `IMPORTANCE_WEIGHT` | | `1.0` | 인기도/참여 지표 가중치 |
| `RECENCY_WEIGHT` | | `0.5` | 24시간 이내 최신성 가중치 |
| `RECENCY_WINDOW_HOURS` | | `24` | 최신성 부스트 적용 시간 창 |
| `MIN_UPVOTES` | | `0` | HF 논문 upvote 하한 (미만 시 인기도 50% 감소) |
| `ENABLE_GEEKNEWS_ENGAGEMENT` | | `true` | GeekNews 토픽 페이지에서 P/댓글 수집 |
| `TRANSLATE_TO_KO` | | `true` | 영문 제목·요약을 한국어로 번역 |
| `KOREAN_SUMMARY_MAX_CHARS` | | `180` | 한국어 요약 최대 글자 수 (2~3문장) |
| `PIAI_THUMBNAIL_URL` | | GitHub raw `assets/piai-logo.png` | 카드 80px 썸네일 HTTPS URL (Teams 렌더링용) |
| `ENABLE_IMAGE_FETCH` | | `false` | `true`면 기사 URL og:image 스크래핑 (기본 비활성) |
| `IMAGE_FETCH_TIMEOUT` | | `5` | og:image fetch 타임아웃(초, ENABLE_IMAGE_FETCH=true 시) |

## 로컬 실행

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows (macOS/Linux: cp .env.example .env)
```

`.env`에 `TEAMS_WEBHOOK_URL`을 설정한 뒤:

```bash
# 실제 Teams 전송
python main.py

# 수집·카드 생성만 확인 (전송 안 함)
python main.py --dry-run
```

## Adaptive Card 형식

- 헤더: `📄📰 오늘의 AI 논문 & 테크 뉴스` (강조 컨테이너)
- **섹션별 그룹**: 📄 Papers · 📰 News · 🔥 Trending · 💬 Community
- 각 항목: 번호 + **제목**, 2~3줄 **요약**, **FactSet**(출처·날짜·Stars/Upvotes), **원문 보기** 링크
- 영문 기사(HF Papers·GitHub 등): `TRANSLATE_TO_KO=true` 시 한국어 제목·요약 표시
- Adaptive Card **v1.4** (Teams Workflows 호환, 썸네일 없음)

### 번역 동작

- `deep-translator`(Google Translate) 사용, **무료·API 키 불필요**
- 영문 비율이 높은 제목·요약만 한국어로 변환 (AI Times 등 한국어 소스는 원문 유지)
- 동일 텍스트는 실행당 **메모리 캐시**로 중복 호출 방지
- 번역 실패 시 **원문(영문) 그대로** 표시

### 썸네일 (PIAI) 정책

- 모든 카드 항목에 **포항공대 인공지능연구원(PIAI) 로고**를 80px 썸네일로 표시합니다.
- 기본 URL: `https://raw.githubusercontent.com/jskh-201910840/teams-news/master/assets/piai-logo.png`
- 공식 로고 출처: `https://piai.postech.ac.kr/webroot/images/korean/layout/logo-v3.png` (저장소 `assets/piai-logo.png`와 동일)
- `PIAI_THUMBNAIL_URL`로 HTTPS URL을 재정의할 수 있습니다. URL이 없거나 유효하지 않으면 텍스트-only 레이아웃으로 폴백합니다.
- **비활성화된 기능**: RSS `<img>`/media 태그, HF paper 썸네일, 기사 og:image 스크래핑 (`ENABLE_IMAGE_FETCH=false` 기본)

## 장애 격리

각 수집기는 독립적으로 실행됩니다. 한 소스(예: GeekNews)가 실패해도 나머지 소스의 뉴스는 정상 발송됩니다.

## 알려진 제약

- **GeekNews**: 루트 `/rss`는 403을 반환할 수 있어 `/rss/news`를 우선 사용합니다.
- **AI Times**: RSS 본문 인코딩이 깨져 보일 수 있으나 제목·링크·날짜는 정상 수집됩니다.
- **Hugging Face**: Daily Papers API는 당일 큐레이션 목록을 반환하며, arXiv 논문은 AI 연구 관련으로 자동 포함됩니다.
- **PyTorch Korea**: `/c/news/14.rss`는 robots.txt에서 `Disallow: /c/*.rss` — `/latest.rss` + 카테고리 필터로 대체.
- **GitHub Trending**: Search API 비인증 rate limit(시간당 ~60회) — 일 1회 cron에 충분. `gh-trending-api.herokuapp.com`은 2026년 기준 404.
- **NAVER D2**: Atom 피드 갱신 주기가 길어 7일 창으로 수집.
- **번역**: Google Translate 비공식 API — 간헐적 rate limit 가능. 실패 시 영문 폴백.

## 라이선스

MIT (필요 시 추가)
