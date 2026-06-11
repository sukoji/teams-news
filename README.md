# Teams AI / Tech News Bot

AI 연구원·개발자를 위한 **AI/테크 뉴스 자동 수집 봇**입니다.  
GeekNews, AI Times, Hugging Face Daily Papers, PyTorch Korea 읽을거리&정보공유에서 최근 24시간 이내 기사를 수집하고, 키워드 필터링 후 Microsoft Teams 채널에 **Adaptive Card**로 발행합니다.

## 저장소 구조

```
teams_news/
├── main.py                      # 진입점: 수집 → 필터 → 이미지·번역 → Teams 전송
├── card_builder.py              # Adaptive Card JSON 생성
├── requirements.txt
├── .env.example
├── .github/workflows/cron.yml   # GitHub Actions 스케줄 (매일 9:00 KST)
├── collectors/
│   ├── base.py                  # NewsItem, BaseCollector
│   ├── geeknews.py              # GeekNews RSS
│   ├── aitimes.py               # AI Times RSS
│   ├── huggingface.py           # HF Daily Papers API
│   └── pytorch_korea.py         # PyTorch Korea 읽을거리&정보공유 RSS
└── utils/
    ├── filters.py               # 24h·키워드 필터, 소스 균형 선별
    ├── translate.py             # 영문 → 한국어 요약 (deep-translator)
    ├── image_fetch.py           # og:image 스크래핑, HF 썸네일
    ├── media.py                 # RSS/HTML 이미지 추출
    └── timezone.py              # KST 타임존
```

## 데이터 소스

| 소스 | URL | 방식 |
|------|-----|------|
| GeekNews | `https://news.hada.io/rss/news` | RSS (403 시 `/rss` 폴백) |
| AI Times | `https://cdn.aitimes.com/rss/gn_rss_allArticle.xml` | RSS |
| Hugging Face Papers | `https://huggingface.co/api/daily_papers` | JSON API |
| PyTorch Korea | `https://discuss.pytorch.kr/c/news/14` (읽을거리&정보공유) | Discourse RSS (`/c/news/14.rss`) |

### 수집·필터 기준

- **시간**: 최근 24시간 이내 게시물 (HF Papers는 Daily API 특성상 48시간 완화)
- **키워드**: AI, LLM, Agent, RAG, Deep Learning, Transformer, 오픈소스 등
- **선별**: 키워드 점수 + **인기도/중요도** + **최신성** 가중 합산 후, **소스별 최소 1건** 보장하여 상위 **5~7건** (기본 7건, 소스당 최대 3건)

### 인기도 신호 (소스별)

| 소스 | 신호 | 비고 |
|------|------|------|
| GeekNews | 토픽 **추천(P)** + **댓글 수** | RSS에 없어 토픽 페이지에서 수집 (`ENABLE_GEEKNEWS_ENGAGEMENT`) |
| AI Times | RSS **노출 순서** | 앞쪽 기사일수록 높은 점수 (조회수 필드 없음) |
| Hugging Face | **upvotes**, **댓글**, **GitHub stars** | Daily Papers API 필드 활용 |
| PyTorch Korea | RSS **노출 순서** | 앞쪽 게시물일수록 높은 점수 (좋아요·댓글은 RSS 미제공) |

최종 점수 = 키워드 관련도 + `IMPORTANCE_WEIGHT` × 인기도 + `RECENCY_WEIGHT` × 최신성(24h 이내). 소스 균형 선별 시 각 소스에서 **가장 높은 점수** 항목을 우선 선택합니다.

## 스케줄 (GitHub Actions)

봇은 **GitHub Actions cron**으로 주기적으로 실행됩니다. 별도 서버나 상시 실행 프로세스는 필요 없습니다.

| 항목 | 값 |
|------|-----|
| 기본 실행 시각 | **매일 9:00 KST** (UTC `0 0 * * *`) |
| 워크플로 파일 | `.github/workflows/cron.yml` |
| 수동 실행 | Actions 탭 → **Daily AI Tech News Bot** → **Run workflow** |

### 스케줄 커스터마이즈

`cron.yml`의 `schedule` 블록을 수정합니다. GitHub Actions cron은 **UTC** 기준입니다.

```yaml
on:
  schedule:
    # 9:00 KST = 00:00 UTC
    - cron: "0 0 * * *"
    # 18:00 KST = 09:00 UTC — 저녁 digest 추가 시 주석 해제
    # - cron: "0 9 * * *"
```

**KST → UTC 변환**: KST = UTC + 9시간. 예) 18:00 KST → 09:00 UTC → `0 9 * * *`

> **참고**: GitHub Actions 스케줄은 몇 분 지연될 수 있습니다. 정확한 시각이 중요하면 자체 서버 cron + `python main.py`를 사용하세요.

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
| `MIN_PER_SOURCE` | | `1` | 소스별 최소 포함 건수 (GeekNews·AI Times·HF·PyTorch Korea 각각) |
| `MAX_PER_SOURCE` | | `3` | 소스별 최대 포함 건수 (HF 독점 방지) |
| `IMPORTANCE_WEIGHT` | | `1.0` | 인기도/참여 지표 가중치 |
| `RECENCY_WEIGHT` | | `0.5` | 24시간 이내 최신성 가중치 |
| `RECENCY_WINDOW_HOURS` | | `24` | 최신성 부스트 적용 시간 창 |
| `MIN_UPVOTES` | | `0` | HF 논문 upvote 하한 (미만 시 인기도 50% 감소) |
| `ENABLE_GEEKNEWS_ENGAGEMENT` | | `true` | GeekNews 토픽 페이지에서 P/댓글 수집 |
| `TRANSLATE_TO_KO` | | `true` | 영문 제목·요약을 한국어로 번역 |
| `KOREAN_SUMMARY_MAX_CHARS` | | `180` | 한국어 요약 최대 글자 수 (2~3문장) |
| `ENABLE_IMAGE_FETCH` | | `true` | 기사 URL에서 og:image 스크래핑 |
| `IMAGE_FETCH_TIMEOUT` | | `5` | 이미지 fetch 타임아웃(초) |

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

- 헤더: `🤖 오늘의 AI/테크 연구 트렌드` (강조 컨테이너)
- 각 항목: **썸네일(있을 때)** + **제목**, 2~3줄 **요약**, 소스별 **아이콘·색상 배지**
- 영문 기사(HF Papers 등): `TRANSLATE_TO_KO=true` 시 한국어 제목·요약 표시
- 하단: 항목별 **원문 보기** 링크
- Adaptive Card **v1.4** (Teams Workflows 호환)

### 번역 동작

- `deep-translator`(Google Translate) 사용, **무료·API 키 불필요**
- 영문 비율이 높은 제목·요약만 한국어로 변환 (AI Times 등 한국어 소스는 원문 유지)
- 동일 텍스트는 실행당 **메모리 캐시**로 중복 호출 방지
- 번역 실패 시 **원문(영문) 그대로** 표시

### 이미지 동작

- RSS feed에 썸네일이 있으면 우선 사용
- 없으면 기사 URL에서 `og:image` 스크래핑 (타임아웃·실패 시 건너뜀)
- HF Papers: API 썸네일 또는 `cdn-thumbnails.huggingface.co` CDN URL
- 이미지 없으면 텍스트만 표시 (카드 레이아웃 유지)

## 장애 격리

각 수집기는 독립적으로 실행됩니다. 한 소스(예: GeekNews)가 실패해도 나머지 소스의 뉴스는 정상 발송됩니다.

## 알려진 제약

- **GeekNews**: 루트 `/rss`는 403을 반환할 수 있어 `/rss/news`를 우선 사용합니다.
- **AI Times**: RSS 본문 인코딩이 깨져 보일 수 있으나 제목·링크·날짜는 정상 수집됩니다.
- **Hugging Face**: Daily Papers API는 당일 큐레이션 목록을 반환하며, arXiv 논문은 AI 연구 관련으로 자동 포함됩니다.
- **PyTorch Korea**: 읽을거리&정보공유 게시판은 Discourse 카테고리 `news`(id 14)이며, `/c/readings`가 아닌 `/c/news/14.rss`를 사용합니다.
- **번역**: Google Translate 비공식 API — 간헐적 rate limit 가능. 실패 시 영문 폴백.
- **이미지**: 일부 사이트는 og:image 미제공 또는 hotlink 차단.

## 라이선스

MIT (필요 시 추가)
