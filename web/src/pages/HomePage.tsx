import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Digest, DigestItem } from "../lib/types";
import { fetchDigest } from "../lib/types";
import { fetchArchiveMeta } from "../lib/archive";
import type { ArchiveMeta } from "../lib/archive";
import { NewsCard } from "../components/NewsCard";
import { SkeletonGrid } from "../components/SkeletonCard";
import { SectionChips, type SectionFilter } from "../components/SectionChips";
import { usePageMeta } from "../hooks/usePageMeta";

function sectionCounts(items: DigestItem[]): Record<string, number> {
  const counts: Record<string, number> = { all: items.length };
  for (const item of items) {
    counts[item.section_id] = (counts[item.section_id] ?? 0) + 1;
  }
  return counts;
}

export function HomePage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [meta, setMeta] = useState<ArchiveMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<SectionFilter>("all");

  usePageMeta({
    title: "오늘의 다이제스트",
    description: "오늘의 AI 논문 & 테크 뉴스 — Papers, News, Trending, Community 큐레이션",
  });

  useEffect(() => {
    fetchDigest()
      .then(setDigest)
      .catch((e: Error) => setError(e.message));
    fetchArchiveMeta()
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  if (error) {
    return (
      <div className="ss-card p-8 text-center text-text-tertiary" role="alert">
        <p className="mb-2 font-medium text-text-primary">다이제스트를 불러오지 못했습니다</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!digest) {
    return (
      <div className="space-y-8">
        <div className="ss-card h-32 animate-pulse bg-surface-subtle" />
        <SkeletonGrid count={4} />
      </div>
    );
  }

  const items =
    filter === "all"
      ? digest.items
      : digest.items.filter((i) => i.section_id === filter);

  const counts = sectionCounts(digest.items);

  return (
    <div className="space-y-8">
      <section className="ss-card relative overflow-hidden p-6 sm:p-8">
        <div className="absolute -right-8 -top-8 size-40 rounded-full bg-brand/5" aria-hidden />
        <div className="absolute -bottom-12 -left-6 size-32 rounded-full bg-brand/5" aria-hidden />
        <div className="relative z-10">
          <p className="ss-section-label mb-2">Daily Digest</p>
          <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
            📄📰 오늘의 AI 논문 &amp; 테크 뉴스
          </h1>
          <p className="text-text-secondary">
            {digest.title} · {digest.item_count}건 · {digest.date}
          </p>
        </div>
      </section>

      {meta && (
        <div
          className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-border bg-surface-subtle px-4 py-3 text-sm text-text-secondary"
          aria-label="아카이브 통계"
        >
          <span>
            <strong className="text-text-primary">{meta.total.toLocaleString()}</strong>건 아카이브
          </span>
          <span aria-hidden>·</span>
          <span>
            <strong className="text-text-primary">{meta.sources.length}</strong>개 소스
          </span>
          <span aria-hidden>·</span>
          <span>
            <strong className="text-text-primary">{Object.keys(meta.date_counts).length}</strong>일
            수집
          </span>
          <Link
            to="/feed"
            className="ml-auto font-medium text-brand no-underline hover:underline touch-target inline-flex items-center"
          >
            전체 피드 보기 →
          </Link>
        </div>
      )}

      <div className="sticky top-[57px] z-40 -mx-4 border-b border-border bg-surface-page px-4 py-3 sm:-mx-6 sm:px-6">
        <SectionChips active={filter} onChange={setFilter} counts={counts} />
      </div>

      {items.length === 0 ? (
        <p className="text-text-tertiary">이 섹션에 항목이 없습니다.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {items.map((item) => (
            <NewsCard key={item.id} item={item} />
          ))}
        </div>
      )}

      {digest.items.length > 0 && (
        <div className="text-center">
          <Link
            to="/feed"
            className="ss-chip ss-chip-active touch-target inline-flex no-underline"
          >
            아카이브 {meta?.total.toLocaleString() ?? ""}건 더 보기 →
          </Link>
        </div>
      )}
    </div>
  );
}
