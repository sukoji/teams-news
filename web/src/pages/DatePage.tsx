import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import type { Digest } from "../lib/types";
import { SITE_BASE, fetchDigest } from "../lib/types";
import { NewsCard } from "../components/NewsCard";
import { SectionChips, type SectionFilter } from "../components/SectionChips";

export function DatePage() {
  const { date } = useParams<{ date: string }>();
  const [digest, setDigest] = useState<Digest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<SectionFilter>("all");

  useEffect(() => {
    if (!date) return;
    const path = `${SITE_BASE}/data/digests/${date}.json`;
    fetch(path)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then(setDigest)
      .catch(() =>
        fetchDigest()
          .then((d) => {
            if (d.date === date) setDigest(d);
            else setError("해당 날짜의 다이제스트를 찾을 수 없습니다.");
          })
          .catch((e: Error) => setError(e.message)),
      );
  }, [date]);

  if (error) {
    return <p className="text-text-tertiary">{error}</p>;
  }

  if (!digest) {
    return <p className="text-text-tertiary">로딩 중…</p>;
  }

  const items =
    filter === "all"
      ? digest.items
      : digest.items.filter((i) => i.section_id === filter);

  const counts: Record<string, number> = { all: digest.items.length };
  for (const item of digest.items) {
    counts[item.section_id] = (counts[item.section_id] ?? 0) + 1;
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="ss-section-label mb-2">Archive</p>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary">{digest.title}</h1>
        <p className="text-text-secondary">
          {digest.date} · {digest.item_count}건
        </p>
      </section>
      <div>
        <SectionChips active={filter} onChange={setFilter} counts={counts} />
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {items.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
