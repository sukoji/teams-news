import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { NewsCard } from "../components/NewsCard";
import {
  PAGE_SIZE,
  SECTION_LABELS,
  fetchArchiveMeta,
  fetchSearchIndex,
  paginate,
  toDigestItem,
} from "../lib/archive";
import type { SearchIndexItem } from "../lib/archive";

export function SectionPage() {
  const { id = "" } = useParams();
  const sectionTitle = SECTION_LABELS[id] ?? id;
  const [items, setItems] = useState<SearchIndexItem[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPage(1);
    Promise.all([fetchArchiveMeta(), fetchSearchIndex()])
      .then(([meta, idx]) => {
        const filtered = idx.items.filter((i) => i.sec === id);
        setItems(filtered);
        const sec = meta.sections.find((s) => s.id === id);
        setCount(sec?.count ?? filtered.length);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const pageItems = paginate(items, page);
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));

  if (loading) {
    return <div className="flex justify-center py-20 text-text-tertiary">로딩 중…</div>;
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="ss-section-label mb-2">Section</p>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary">{sectionTitle}</h1>
        <p className="text-text-secondary">
          {count.toLocaleString()}건 ·{" "}
          <Link to="/feed" className="text-brand no-underline hover:underline">
            전체 피드
          </Link>
        </p>
      </section>

      {pageItems.length === 0 ? (
        <p className="text-text-tertiary">이 섹션의 아카이브 항목이 없습니다.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {pageItems.map((item, i) => (
            <NewsCard key={item.id} item={toDigestItem(item, (page - 1) * PAGE_SIZE + i + 1)} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <nav className="flex items-center justify-center gap-2 pt-4">
          <button
            type="button"
            disabled={page <= 1}
            className="ss-chip disabled:opacity-40"
            onClick={() => setPage((p) => p - 1)}
          >
            ← 이전
          </button>
          <span className="text-sm text-text-tertiary">
            {page} / {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            className="ss-chip disabled:opacity-40"
            onClick={() => setPage((p) => p + 1)}
          >
            다음 →
          </button>
        </nav>
      )}
    </div>
  );
}
