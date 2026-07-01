# Teams AI / Tech News Bot

AI 연구원·개발자를 위한 **AI/테크 뉴스 자동 수집 봇 + 웹 다이제스트 + 누적 아카이브**입니다.  
GeekNews, AI Times, Hugging Face Daily Papers, PyTorch Korea, **GitHub Trending**, **전자신문 IT**, **NAVER D2**, **ZDNet Korea**, **Elvis AI Newsletter**에서 기사·레포를 **매시간 수집·누적**하고, 키워드 매칭 항목은 **아카이브에 영구 저장**됩니다. 매일 **섹션 균형 Top 7**은 Microsoft Teams 카드·일일 다이제스트로 발행합니다.

## 웹 사이트 & RSS

| 항목 | URL |
|------|-----|
| **웹 다이제스트 (오늘 Top 7)** | `https://sukoji.github.io/teams-news/` |
| **전체 피드 (아카이브)** | `https://sukoji.github.io/teams-news/feed` |
| **검색** | `https://sukoji.github.io/teams-news/search?q=LLM` |
| **RSS (아카이브 최신 50)** | `https://sukoji.github.io/teams-news/feed.xml` |
| **RSS (일일 Top 7)** | `https://sukoji.github.io/teams-news/feed/daily.xml` |
| **JSON API (다이제스트)** | `https://sukoji.github.io/teams-news/data/latest.json` |
| **검색 인덱스 JSON** | `https://sukoji.github.io/teams-news/data/archive/search-index.json` |
| **구독 페이지** | `https://sukoji.github.io/teams-news/subscribe` |

섹션별 RSS (아카이브 기준): `/feed/papers.xml` · `/feed/news.xml` · `/feed/trending.xml` · `/feed/community.xml`

> GitHub Pages 최초 배포 후 Settings → Pages → Source를 **GitHub Actions**로 설정하세요.

### 웹 페이지

| 경로 | 설명 |
|------|------|
| `/` | 오늘의 Top 7 하이라이트 + 전체 피드 링크 |
| `/feed` | 아카이브 전체 — 페이지네이션, 필터, 정렬 |
| `/search?q=…&source=…&section=…&from=…` | 전문 검색 + 필터 칩 |
| `/source/geeknews` | 소스별 아카이브 |
| `/section/papers` | 섹션별 아카이브 |
| `/archive` | 날짜별 다이제스트 (수집·다이제스트 건수 표시) |

헤더에 **고정 검색창** · **`/` 키**로 검색 포커스 · 모바일 **필터 드로어** 지원.

### 봇 개발자용 RSS 필드

각 `<item>`:

| 필드 | 설명 |
|------|------|
| `title` | 한국어 제목 (가능 시) |
| `link` | **원문 URL** (본문 미포함) |
| `description` | 한국어/영문 요약 |
| `pubDate` | RFC 822 게시 시각 |
| `category` | `papers` \| `news` \| `trending` \| `community` |
| `source` | 출처명 |
| `guid` | `SHA-256(url\|date)` — 중복 감지용 |

`feed/full.xml` 추가 네임스페이스: `teams:score`, `teams:engagement`, `teams:section`, `teams:titleOriginal`

## 저장소 구조

```
teams_news/
├── main.py                      # --ingest | --digest | --export | --teams
├── card_builder.py              # Adaptive Card JSON (Teams)
├── outputs/
│   ├── archive.py               # items.jsonl + search-index.json (누적 아카이브)
│   ├── export.py                # data/digests/*.json (일일 Top 7)
│   └── rss_builder.py           # feed.xml (아카이브) + feed/daily.xml (Top 7)
├── data/
│   ├── archive/                 # items.jsonl, search-index.json, meta.json
│   └── digests/                 # YYYY-MM-DD.json, latest.json, archive-index.json
├── web/                         # Vite + React + Tailwind (StyleSeed Linear)
│   ├── src/pages/               # Home, Feed, Search, Source, Section, Archive…
│   └── public/data/archive/     # GitHub Pages 정적 데이터
├── .github/workflows/
│   ├── ingest.yml               # 매시간 아카이브 수집
│   └── cron.yml                 # 매일 Top 7 + Teams + Pages 배포
├── collectors/ …
└── utils/ …
```

## 데이터 모델

### 아카이브 (`data/archive/items.jsonl`)

키워드 매칭 항목을 **URL 해시 기준 dedupe**하여 append-only JSONL로 저장합니다.

| 필드 | 설명 |
|------|------|
| `id` | `SHA-256(normalized_url)[:32]` |
| `title`, `title_ko` | 원문·한국어 제목 |
| `summary`, `summary_ko` | 요약 |
| `url`, `source`, `source_slug` | 원문 URL·출처 |
| `section`, `section_id` | papers / news / trending / community |
| `published_at` | 원문 게시 시각 (KST ISO) |
| `collected_at` | 수집 시각 |
| `score`, `importance_score` | 키워드·인기·최신성 점수 |
| `popularity`, `upvotes` | 소스별 참여 지표 |
| `matched_keywords`, `engagement` | 매칭 키워드·표시용 지표 |

매 ingest 실행 시 `search-index.json`(클라이언트 검색용)과 `meta.json`(소스·섹션·날짜별 건수)을 재생성합니다.

### 일일 다이제스트 (`data/digests/YYYY-MM-DD.json`)

Teams 카드용 **큐레이션 Top 7** (섹션 균형). 기존 스키마 유지.

### 검색 인덱스 규모 한도

- 클라이언트 fuse.js 검색 — **~10,000건**까지 권장 (그 이상은 search-index 분할 또는 서버 검색 검토)
- RSS `feed.xml` — 아카이브 **최신 50건**

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
| Elvis AI Newsletter | `https://nlp.elvissaravia.com/feed` | RSS (Substack) |

### robots.txt 준수

각 소스의 `robots.txt`를 확인하고, 허용된 경로·방식만 사용합니다.

| 소스 | robots.txt | 허용 경로 (봇이 사용) | 비허용·조정 |
|------|------------|----------------------|-------------|
| **GeekNews** (`news.hada.io`) | `User-agent: *` → `Allow: /` | `/rss/news`, `/rss` (RSS) | `/topic?id=` (인기도) — **기본 비활성** (`ENABLE_GEEKNEWS_ENGAGEMENT=false`); `/api/`, `/auth/` 등 — 미사용 |
| **AI Times** (`aitimes.com`, `cdn.aitimes.com`) | `Disallow: /admin/` only | `cdn.aitimes.com/rss/*.xml` (RSS) | 기사 HTML·og:image 스크래핑 — **비활성** |
| **Hugging Face** (`huggingface.co`) | `Allow: /` | `/api/daily_papers` (JSON API) | 논문 썸네일 CDN — **카드에 미사용** |
| **PyTorch Korea** (`discuss.pytorch.kr`) | `Disallow: /c/*.rss`, `/t/*/*.rss` | `/latest.rss` (사이트 전체 최신 RSS) | `/c/news/14.rss` — **robots.txt 위반** → `/latest.rss`에서 `읽을거리&정보공유` 카테고리만 필터 |
| **GitHub Trending** (`api.github.com`) | Search API 허용 | `/search/repositories` (인증 없이 일 1회 수준) | `github.com/trending` HTML 스크래핑·Heroku API — **미사용** |
| **전자신문** (`rss.etnews.com`) | `User-agent: *` → `Allow: /` (2026-06-25 확인) | `rss.etnews.com/Section901.xml` | 기사 HTML 스크래핑 — **미사용** |
| **NAVER D2** (`d2.naver.com`) | robots.txt **404** — RFC 9309상 전 경로 허용 (2026-06-25 확인) | `/d2.atom` (Atom) | — |
| **ZDNet Korea** (`feeds.feedburner.com`) | 유효 robots.txt 없음 (HTML 응답) | `feeds.feedburner.com/zdkorea` | FeedBurner 공개 RSS |
| **Elvis AI Newsletter** (`nlp.elvissaravia.com`) | `Disallow: /feed/private` only — public `/feed` 허용 (2026-07-01 확인) | `nlp.elvissaravia.com/feed` (RSS) | Substack excerpt만 사용 |

> **썸네일**: 기사별 썸네일·og:image 수집·표시를 사용하지 않습니다 (`ENABLE_IMAGE_FETCH=false` 기본). 카드는 텍스트·FactSet 중심 레이아웃입니다.

**User-Agent**: `PIAI-TeamsNews/1.0 (+https://sukoji.github.io/teams-news/about)` — 모든 HTTP 수집 요청에 사용합니다.

**CI 검증**: PR/push 시 [`Collection Compliance`](.github/workflows/compliance.yml) 워크플로가 `python scripts/check_robots.py`를 실행합니다. 웹훅 변경 전 요약은 [`COMPLIANCE.md`](COMPLIANCE.md)를 참고하세요.

### 수집·필터 기준

- **시간**: 최근 24시간 이내 게시물 (HF Papers 48h, NAVER D2·GitHub Trending·Elvis AI Newsletter 7일 완화)
- **키워드**: AI, LLM, Agent, RAG, Deep Learning, Transformer, 오픈소스 등
- **선별**: 키워드 점수 + **인기도/중요도** + **최신성** 가중 합산 후, **소스별 최소 1건** 보장하여 상위 **5~7건** (기본 7건, 소스당 최대 3건)

### 인기도 신호 (소스별)

| 소스 | 신호 | 비고 |
|------|------|------|
| GeekNews | 토픽 **추천(P)** + **댓글 수** | RSS에 없어 토픽 페이지에서 수집 — **기본 비활성** (`ENABLE_GEEKNEWS_ENGAGEMENT=false`, 0.3s 간격) |
| AI Times | RSS **노출 순서** | 앞쪽 기사일수록 높은 점수 (조회수 필드 없음) |
| Hugging Face | **upvotes**, **댓글**, **GitHub stars** | Daily Papers API 필드 활용 |
| PyTorch Korea | RSS **노출 순서** | 앞쪽 게시물일수록 높은 점수 (좋아요·댓글은 RSS 미제공) |
| GitHub Trending | **GitHub stars** | Search API `stargazers_count`, 5,000 stars 초과 mega-repo 제외 |
| 전자신문 IT / NAVER D2 / ZDNet Korea / Elvis AI Newsletter | RSS **노출 순서** | 앞쪽 기사일수록 높은 점수 |

최종 점수 = 키워드 관련도 + `IMPORTANCE_WEIGHT` × 인기도 + `RECENCY_WEIGHT` × 최신성(24h 이내). 소스 균형 선별 시 각 소스에서 **가장 높은 점수** 항목을 우선 선택합니다.

## 스케줄 (GitHub Actions)

두 워크플로로 분리됩니다.

| 워크플로 | cron (UTC) | 명령 | 역할 |
|----------|------------|------|------|
| **Hourly Archive Ingest** (`ingest.yml`) | `0 * * * *` (매시 정각) | `python main.py --ingest` | 키워드 매칭 항목 아카이브 append, search-index, RSS |
| **Daily AI Tech News Bot** (`cron.yml`) | `0 23 * * *` (~10:00 KST) | `python main.py --digest` | ingest + Top 7 export + Teams + GitHub Pages |

| 항목 | 값 |
|------|-----|
| 일일 도착 시각 | **매일 ~10:00 KST** (UTC `0 23 * * *`, GitHub 지연 ~2h 보정) |
| 수동 실행 | Actions 탭 → 해당 워크플로 → **Run workflow** |

> **GitHub Actions 지연**: cron은 UTC 기준이며, 실제 실행은 **수 분~수 시간** 늦게 시작될 수 있습니다.

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
| `ENABLE_GEEKNEWS_ENGAGEMENT` | | `false` | `true`면 GeekNews 토픽 페이지에서 P/댓글 수집 (0.3s 간격) |
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
# 매시간 아카이브 수집 (Teams·다이제스트 없음)
python main.py --ingest

# 일일 다이제스트: ingest + Top 7 export + Teams
python main.py --digest

# Teams + JSON/RSS export (ingest 포함)
python main.py --all

# Teams만 (Top 7)
python main.py --teams

# JSON/RSS export만 (Top 7 + daily.xml)
python main.py --export

# 번역 생략 (로컬 테스트용)
python main.py --ingest --no-translate

# 수집·카드·export 확인 (Teams 미전송)
python main.py --export --dry-run
python main.py --ingest --dry-run
```

### 웹 UI 로컬 개발

```bash
cd web
npm install
npm run dev      # http://localhost:5173/teams-news/
npm run build    # dist/ → GitHub Pages 아티팩트
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
- 기본 URL: `https://raw.githubusercontent.com/sukoji/teams-news/master/assets/piai-logo.png`
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
- **Elvis AI Newsletter**: 주간 발행(Substack)이라 7일 창으로 수집. RSS excerpt만 사용.
- **번역**: Google Translate 비공식 API — 간헐적 rate limit 가능. 실패 시 영문 폴백.

## 라이선스

MIT (필요 시 추가)
