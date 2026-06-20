import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { FilterPanel } from "../components/FilterPanel";
import { NewsCard } from "../components/NewsCard";
import {
  PAGE_SIZE,
  fetchArchiveMeta,
  fetchSearchIndex,
  filterItems,
  filtersToSearchParams,
  paginate,
  parseFilters,
  searchArchive,
  toDigestItem,
} from "../lib/archive";
import type { ArchiveMeta, FeedFilters, SearchIndexItem } from "../lib/archive";

export function FeedPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const basePath = location.pathname.includes("/search") ? "/search" : "/feed";
  const navigate = useNavigate();
  const filters = parseFilters(searchParams);
  const [meta, setMeta] = useState<ArchiveMeta | null>(null);
  const [items, setItems] = useState<SearchIndexItem[]>([]);
  const [filtered, setFiltered] = useState<SearchIndexItem[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchArchiveMeta(), fetchSearchIndex()])
      .then(([m, idx]) => {
        setMeta(m);
        setItems(idx.items);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setPage(1);
  }, [searchParams.toString()]);

  useEffect(() => {
    if (!items.length) return;
    let cancelled = false;

    (async () => {
      const fuseResults = filters.q ? await searchArchive(items, filters.q) : undefined;
      if (cancelled) return;
      setFiltered(filterItems(items, filters, fuseResults));
    })();

    return () => {
      cancelled = true;
    };
  }, [items, filters.q, filters.source, filters.section, filters.from, filters.to, filters.sort]);

  const applyFilters = useCallback(
    (next: FeedFilters) => {
      const params = filtersToSearchParams(next);
      navigate(`${basePath}?${params.toString()}`);
    },
    [navigate, basePath],
  );

  const pageItems = paginate(filtered, page);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  if (error) {
    return (
      <div className="ss-card p-8 text-center text-text-tertiary">
        피드를 불러오지 못했습니다. {error}
      </div>
    );
  }

  if (loading) {
    return <div className="flex justify-center py-20 text-text-tertiary">로딩 중…</div>;
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="ss-section-label mb-2">Archive Feed</p>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-text-primary">전체 피드</h1>
        <p className="text-text-secondary">
          키워드 매칭 아카이브 {meta?.total.toLocaleString() ?? 0}건 · 시간별 수집 ·{" "}
          <Link to="/search" className="text-brand no-underline hover:underline">
            고급 검색
          </Link>
        </p>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr]">
        <aside>
          <FilterPanel meta={meta} filters={filters} onChange={applyFilters} />
        </aside>

        <div className="space-y-4">
          <p className="text-sm text-text-tertiary">
            {filtered.length.toLocaleString()}건
            {filters.q && ` · "${filters.q}"`}
          </p>

          {pageItems.length === 0 ? (
            <p className="text-text-tertiary">조건에 맞는 항목이 없습니다.</p>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {pageItems.map((item, i) => (
                <NewsCard key={item.id} item={toDigestItem(item, (page - 1) * PAGE_SIZE + i + 1)} />
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <nav className="flex items-center justify-center gap-2 pt-4" aria-label="Pagination">
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
      </div>
    </div>
  );
}
