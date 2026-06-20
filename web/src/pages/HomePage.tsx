import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Digest, DigestItem } from "../lib/types";
import { fetchDigest } from "../lib/types";
import { fetchArchiveMeta } from "../lib/archive";
import { NewsCard } from "../components/NewsCard";
import { SectionChips, type SectionFilter } from "../components/SectionChips";

function sectionCounts(items: DigestItem[]): Record<string, number> {
  const counts: Record<string, number> = { all: items.length };
  for (const item of items) {
    counts[item.section_id] = (counts[item.section_id] ?? 0) + 1;
  }
  return counts;
}

export function HomePage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [archiveTotal, setArchiveTotal] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<SectionFilter>("all");

  useEffect(() => {
    fetchDigest()
      .then(setDigest)
      .catch((e: Error) => setError(e.message));
    fetchArchiveMeta()
      .then((m) => setArchiveTotal(m.total))
      .catch(() => setArchiveTotal(null));
  }, []);

  if (error) {
    return (
      <div className="ss-card p-8 text-center text-text-tertiary">
        다이제스트를 불러오지 못했습니다. {error}
      </div>
    );
  }

  if (!digest) {
    return (
      <div className="flex justify-center py-20 text-text-tertiary">로딩 중…</div>
    );
  }

  const items =
    filter === "all"
      ? digest.items
      : digest.items.filter((i) => i.section_id === filter);

  const counts = sectionCounts(digest.items);

  return (
    <div className="space-y-8">
      {/* Hero — StyleSeed §14 type D */}
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
            {archiveTotal != null && (
              <>
                {" "}
                ·{" "}
                <Link to="/feed" className="text-brand no-underline hover:underline">
                  전체 피드 {archiveTotal.toLocaleString()}건 →
                </Link>
              </>
            )}
          </p>
        </div>
      </section>

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
    </div>
  );
}
