import { useState } from "react";
import { FEED_URLS } from "../lib/types";
import { SectionCard } from "../styleseed/components/patterns/section-card";

const FEEDS = [
  { name: "전체 아카이브", url: FEED_URLS.all, desc: "아카이브 최신 50건 RSS 2.0" },
  { name: "일일 Top 7", url: FEED_URLS.daily, desc: "오늘의 큐레이션 다이제스트 (Teams 카드)" },
  { name: "확장 메타데이터", url: FEED_URLS.full, desc: "점수·섹션·참여 지표 포함 (봇 개발용)" },
  { name: "📄 Papers", url: FEED_URLS.papers, desc: "Hugging Face Daily Papers" },
  { name: "📰 News", url: FEED_URLS.news, desc: "GeekNews, AI Times, ETNews, NAVER D2, ZDNet" },
  { name: "🔥 Trending", url: FEED_URLS.trending, desc: "GitHub ML/AI 레포" },
  { name: "💬 Community", url: FEED_URLS.community, desc: "PyTorch Korea" },
  { name: "JSON API", url: FEED_URLS.json, desc: "구조화된 최신 다이제스트 (REST-style static JSON)" },
  { name: "아카이브 검색 인덱스", url: FEED_URLS.archive, desc: "전체 수집 아카이브 검색용 JSON" },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    const absolute = text.startsWith("http") ? text : `${window.location.origin}${text}`;
    await navigator.clipboard.writeText(absolute);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button type="button" onClick={copy} className="ss-chip ss-chip-active !text-xs">
      {copied ? "복사됨 ✓" : "URL 복사"}
    </button>
  );
}

export function SubscribePage() {
  const origin = typeof window !== "undefined" ? window.location.origin : "";

  return (
    <div className="space-y-8">
      <section>
        <p className="ss-section-label mb-2">Feeds</p>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary">RSS &amp; API 구독</h1>
        <p className="max-w-2xl text-text-secondary">
          봇·알림·리더 앱 개발을 위한 피드 URL입니다. 각 항목은 원문 링크, 한국어 요약(가능 시),
          섹션, 안정적인 GUID( URL+날짜 해시 )를 포함합니다.
        </p>
      </section>

      <div className="space-y-3">
        {FEEDS.map((feed) => {
          const displayUrl = feed.url.startsWith("http")
            ? feed.url
            : `${origin}${feed.url}`;
          return (
            <div
              key={feed.url}
              className="ss-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <h2 className="font-semibold text-text-primary">{feed.name}</h2>
                <p className="text-sm text-text-tertiary">{feed.desc}</p>
                <code className="mt-2 block break-all text-xs text-brand">{displayUrl}</code>
              </div>
              <CopyButton text={displayUrl} />
            </div>
          );
        })}
      </div>

      <SectionCard title="봇 개발자 가이드">
        <ul className="list-inside list-disc space-y-2 text-sm text-text-secondary">
          <li>
            <strong className="text-text-primary">guid</strong>: SHA-256(url|date) —
            중복 감지에 사용
          </li>
          <li>
            <strong className="text-text-primary">category</strong>: papers | news |
            trending | community
          </li>
          <li>
            <strong className="text-text-primary">full.xml</strong>: teams:score,
            teams:engagement 네임스페이스 확장 필드
          </li>
          <li>본문 전문 미포함 — 원문 URL로만 연결 (저작권·robots.txt 준수)</li>
        </ul>
      </SectionCard>
    </div>
  );
}
