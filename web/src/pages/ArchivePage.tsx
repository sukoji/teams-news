import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Digest } from "../lib/types";
import { SITE_BASE, fetchArchiveDates, fetchDigest } from "../lib/types";
import type { ArchiveIndex } from "../lib/archive";
import { Badge } from "../styleseed/components/ui/badge";
import { usePageMeta } from "../hooks/usePageMeta";

async function fetchArchiveIndex(): Promise<ArchiveIndex> {
  const res = await fetch(`${SITE_BASE}/data/archive-index.json`);
  if (!res.ok) return { dates: [] };
  return res.json() as Promise<ArchiveIndex>;
}

export function ArchivePage() {
  const [index, setIndex] = useState<ArchiveIndex>({ dates: [] });
  const [latest, setLatest] = useState<Digest | null>(null);

  usePageMeta({
    title: "아카이브",
    description: "날짜별 AI·테크 뉴스 다이제스트 아카이브",
  });

  useEffect(() => {
    fetchArchiveIndex().then(setIndex);
    fetchArchiveDates().then((dates) => {
      if (dates.length && !index.dates.length) {
        setIndex((prev) => ({ ...prev, dates }));
      }
    });
    fetchDigest().then(setLatest);
  }, []);

  const list = index.dates.length > 0 ? index.dates : latest ? [latest.date] : [];

  return (
    <div className="space-y-8">
      <section>
        <p className="ss-section-label mb-2">History</p>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary">아카이브</h1>
        <p className="text-text-secondary">
          날짜별 다이제스트 (Top 7) ·{" "}
          <Link to="/feed" className="text-brand no-underline hover:underline">
            전체 피드
          </Link>{" "}
          ·{" "}
          <code className="rounded bg-surface-subtle px-1.5 py-0.5 text-xs text-text-primary">
            {SITE_BASE}/data/digests/YYYY-MM-DD.json
          </code>
        </p>
      </section>

      <ul className="space-y-2">
        {list.map((date) => {
          const digestCount = index.digest_counts?.[date];
          const archiveCount = index.archive_counts?.[date];
          return (
            <li key={date}>
              <Link
                to={`/date/${date}`}
                className="ss-card flex items-center justify-between gap-3 px-4 py-3 no-underline"
              >
                <div className="flex flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-3">
                  <span className="font-medium text-text-primary">{date}</span>
                  {(digestCount != null || archiveCount != null) && (
                    <span className="text-xs text-text-tertiary">
                      {digestCount != null && `다이제스트 ${digestCount}건`}
                      {digestCount != null && archiveCount != null && " · "}
                      {archiveCount != null && `수집 ${archiveCount}건`}
                    </span>
                  )}
                </div>
                {latest?.date === date && (
                  <Badge variant="secondary" className="bg-brand-tint text-brand border-transparent">
                    최신
                  </Badge>
                )}
              </Link>
            </li>
          );
        })}
      </ul>

      {list.length === 0 && (
        <p className="text-text-tertiary">아카이브 데이터가 아직 없습니다.</p>
      )}
    </div>
  );
}
