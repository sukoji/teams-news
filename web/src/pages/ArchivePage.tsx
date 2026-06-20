import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Digest } from "../lib/types";
import { SITE_BASE, fetchArchiveDates, fetchDigest } from "../lib/types";
import { Badge } from "../styleseed/components/ui/badge";

export function ArchivePage() {
  const [dates, setDates] = useState<string[]>([]);
  const [latest, setLatest] = useState<Digest | null>(null);

  useEffect(() => {
    fetchArchiveDates().then(setDates);
    fetchDigest().then(setLatest);
  }, []);

  const list = dates.length > 0 ? dates : latest ? [latest.date] : [];

  return (
    <div className="space-y-8">
      <section>
        <p className="ss-section-label mb-2">History</p>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary">아카이브</h1>
        <p className="text-text-secondary">
          날짜별 다이제스트 JSON ·{" "}
          <code className="rounded bg-surface-subtle px-1.5 py-0.5 text-xs text-text-primary">
            {SITE_BASE}/data/digests/YYYY-MM-DD.json
          </code>
        </p>
      </section>

      <ul className="space-y-2">
        {list.map((date) => (
          <li key={date}>
            <Link
              to={`/date/${date}`}
              className="ss-card flex items-center justify-between px-4 py-3 no-underline"
            >
              <span className="font-medium text-text-primary">{date}</span>
              {latest?.date === date && (
                <Badge variant="secondary" className="bg-brand-tint text-brand border-transparent">
                  최신
                </Badge>
              )}
            </Link>
          </li>
        ))}
      </ul>

      {list.length === 0 && (
        <p className="text-text-tertiary">아카이브 데이터가 아직 없습니다.</p>
      )}
    </div>
  );
}
