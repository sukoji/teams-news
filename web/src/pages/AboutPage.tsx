import { SectionCard } from "../styleseed/components/patterns/section-card";
import { usePageMeta } from "../hooks/usePageMeta";

export function AboutPage() {
  usePageMeta({
    title: "About",
    description: "PIAI Teams News — AI·테크 뉴스 큐레이션 정책 및 GeekNews 비교",
  });

  return (
    <div className="max-w-2xl space-y-8">
      <section>
        <p className="ss-section-label mb-2">About</p>
        <h1 className="mb-4 text-2xl font-bold tracking-tight text-text-primary">PIAI Teams News</h1>
        <p className="text-text-secondary">
          <strong className="text-text-primary">PIAI Teams News</strong>는 포항공대
          인공지능연구원(PIAI)에서 운영하는 AI·테크 뉴스 큐레이션 서비스입니다. GeekNews, AI Times,
          Hugging Face Daily Papers, GitHub Trending, PyTorch Korea, 전자신문 IT, NAVER D2, ZDNet
          Korea 등 <strong className="text-text-primary">robots.txt를 준수하는</strong>{" "}
          공개 RSS/API만 사용합니다.
        </p>
      </section>

      <SectionCard title="큐레이션 정책">
        <ul className="list-inside list-disc space-y-2 text-sm text-text-secondary">
          <li>본 사이트는 <strong className="text-text-primary">링크·요약만</strong> 제공하며, 기사 전문을 재게시하지 않습니다.</li>
          <li>모든 항목은 원문 URL로 연결됩니다 — 저작권은 각 출처에 있습니다.</li>
          <li>기사 썸네일·og:image는 표시하지 않습니다 (팀 정책).</li>
          <li>영문 콘텐츠는 한국어 제목·요약으로 번역해 가독성을 높입니다.</li>
        </ul>
      </SectionCard>

      <SectionCard title="GeekNews와의 차이">
        <ul className="list-inside list-disc space-y-2 text-sm text-text-secondary">
          <li>섹션별 균형 선별 (Papers · News · Trending · Community)</li>
          <li>참여 지표 표시 (Stars, Upvotes, Points)</li>
          <li>한국어 요약 + 다크/라이트 모드 + 모바일 퍼스트 UI</li>
          <li>섹션별 RSS + JSON API + 확장 메타데이터 피드</li>
        </ul>
      </SectionCard>

      <SectionCard title="Microsoft Teams">
        <p className="text-sm text-text-secondary">
          매일 Teams 채널에 Adaptive Card 형태로 동일 다이제스트가 발송됩니다. 웹·RSS·Teams는 동일
          파이프라인에서 생성됩니다.
        </p>
        <p className="mt-4 text-xs text-text-tertiary">
          소스 코드:{" "}
          <a
            href="https://github.com/jskh-201910840/teams-news"
            className="text-brand no-underline hover:underline"
            target="_blank"
            rel="noreferrer"
          >
            github.com/jskh-201910840/teams-news
          </a>
        </p>
      </SectionCard>
    </div>
  );
}
