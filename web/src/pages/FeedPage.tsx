import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { FilterPanel } from "../components/FilterPanel";
import { NewsCard } from "../components/NewsCard";
import { SkeletonGrid } from "../components/SkeletonCard";
import { usePageMeta } from "../hooks/usePageMeta";
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
import {
  SEARCH_SUGGESTIONS,
  loadRecentSearches,
} from "../lib/recentSearches";

const LAST_VISIT_KEY = "teams-news-last-visit";
const LAST_TOTAL_KEY = "teams-news-last-total";

function countNewSinceLastVisit(total: number): number | null {
  try {
    const lastTotal = localStorage.getItem(LAST_TOTAL_KEY);
    if (lastTotal == null) return null;
    const diff = total - parseInt(lastTotal, 10);
    return diff > 0 ? diff : null;
  } catch {
    return null;
  }
}

function recordVisit(total: number) {
  try {
    localStorage.setItem(LAST_VISIT_KEY, new Date().toISOString());
    localStorage.setItem(LAST_TOTAL_KEY, String(total));
  } catch {
    /* ignore */
  }
}

function SearchEmptyPrompt({ onSearch }: { onSearch: (q: string) => void }) {
  const recent = useMemo(() => loadRecentSearches(), []);

  return (
    <div className="ss-card p-8 text-center">
      <p className="text-lg font-medium text-text-primary">검색어를 입력하세요</p>
      <p className="mt-2 text-sm text-text-tertiary">
        상단 검색창에 키워드를 입력하면 결과가 바로 표시됩니다.
      </p>
      {(recent.length > 0 || SEARCH_SUGGESTIONS.length > 0) && (
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {recent.map((term) => (
            <button
              key={term}
              type="button"
              className="ss-chip touch-target"
              onClick={() => onSearch(term)}
            >
              {term}
            </button>
          ))}
          {SEARCH_SUGGESTIONS.filter((s) => !recent.includes(s)).map((term) => (
            <button
              key={term}
              type="button"
              className="ss-chip touch-target"
              onClick={() => onSearch(term)}
            >
              {term}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function NoResultsState({
  query,
  hasFilters,
  onClear,
  onSearch,
}: {
  query: string;
  hasFilters: boolean;
  onClear: () => void;
  onSearch: (q: string) => void;
}) {
  const recent = useMemo(
    () => loadRecentSearches().filter((r) => r.toLowerCase() !== query.toLowerCase()),
    [query],
  );

  return (
    <div className="ss-card p-8 text-center">
      <p className="text-lg font-medium text-text-primary">결과 없음</p>
      <p className="mt-2 text-sm text-text-tertiary">
        &ldquo;{query}&rdquo;에 맞는 항목이 없습니다. 다른 키워드를 시도해 보세요.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {hasFilters && (
          <button type="button" className="ss-chip ss-chip-active touch-target" onClick={onClear}>
            필터 초기화
          </button>
        )}
        {recent.slice(0, 4).map((term) => (
          <button
            key={term}
            type="button"
            className="ss-chip touch-target"
            onClick={() => onSearch(term)}
          >
            {term}
          </button>
        ))}
        {SEARCH_SUGGESTIONS.filter(
          (s) => s.toLowerCase() !== query.toLowerCase() && !recent.includes(s),
        )
          .slice(0, 3)
          .map((term) => (
            <button
              key={term}
              type="button"
              className="ss-chip touch-target"
              onClick={() => onSearch(term)}
            >
              {term}
            </button>
          ))}
      </div>
    </div>
  );
}

export function FeedPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const isSearch = location.pathname.includes("/search");
  const basePath = isSearch ? "/search" : "/feed";
  const navigate = useNavigate();
  const filters = parseFilters(searchParams);
  const page = filters.page ?? 1;
  const [meta, setMeta] = useState<ArchiveMeta | null>(null);
  const [items, setItems] = useState<SearchIndexItem[]>([]);
  const [filtered, setFiltered] = useState<SearchIndexItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newCount, setNewCount] = useState<number | null>(null);

  const hasExtraFilters = !!(filters.source || filters.section || filters.from || filters.to);
  const awaitingQuery = isSearch && !filters.q;

  usePageMeta({
    title: isSearch ? (filters.q ? `"${filters.q}" 검색` : "검색") : "전체 피드",
    description: isSearch
      ? `PIAI Teams News 아카이브에서 "${filters.q ?? ""}" 검색 결과`
      : "키워드 매칭 AI·테크 뉴스 아카이브 — Papers, News, Trending, Community",
  });

  useEffect(() => {
    Promise.all([fetchArchiveMeta(), fetchSearchIndex()])
      .then(([m, idx]) => {
        setMeta(m);
        setItems(idx.items);
        setNewCount(countNewSinceLastVisit(m.total));
        recordVisit(m.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!items.length) return;
    if (awaitingQuery) {
      setFiltered([]);
      setSearching(false);
      return;
    }

    let cancelled = false;
    setSearching(true);

    (async () => {
      const fuseResults = filters.q ? await searchArchive(items, filters.q) : undefined;
      if (cancelled) return;
      setFiltered(filterItems(items, filters, fuseResults));
      setSearching(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [items, filters.q, filters.source, filters.section, filters.from, filters.to, filters.sort, awaitingQuery]);

  const applyFilters = useCallback(
    (next: FeedFilters) => {
      const params = filtersToSearchParams(next);
      navigate(`${basePath}?${params.toString()}`);
    },
    [navigate, basePath],
  );

  const goToPage = useCallback(
    (nextPage: number) => {
      applyFilters({ ...filters, page: nextPage });
    },
    [applyFilters, filters],
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageItems = useMemo(
    () => paginate(filtered, safePage),
    [filtered, safePage],
  );

  if (error) {
    return (
      <div className="ss-card p-8 text-center text-text-tertiary" role="alert">
        <p className="mb-2 font-medium text-text-primary">피드를 불러오지 못했습니다</p>
        <p className="text-sm">{error}</p>
        <p className="mt-2 text-xs">오프라인이거나 데이터가 아직 배포되지 않았을 수 있습니다.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="h-4 w-24 animate-pulse rounded bg-surface-subtle" />
          <div className="h-8 w-48 animate-pulse rounded bg-surface-subtle" />
        </div>
        <SkeletonGrid count={4} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="ss-section-label mb-2">{isSearch ? "Search" : "Archive Feed"}</p>
        <div className="mb-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            {isSearch ? "검색" : "전체 피드"}
          </h1>
          {newCount != null && !isSearch && (
            <span className="rounded-full bg-brand-tint px-2.5 py-0.5 text-xs font-semibold text-brand">
              +{newCount} 신규
            </span>
          )}
        </div>
        <p className="text-text-secondary">
          키워드 매칭 아카이브 {meta?.total.toLocaleString() ?? 0}건 ·{" "}
          {meta?.sources.length ?? 0}개 소스 ·{" "}
          {!isSearch && (
            <>
              <Link to="/search" className="text-brand no-underline hover:underline">
                고급 검색
              </Link>
            </>
          )}
          {isSearch && (
            <Link to="/feed" className="text-brand no-underline hover:underline">
              전체 피드
            </Link>
          )}
        </p>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr]">
        <aside aria-label="필터">
          <FilterPanel meta={meta} filters={filters} onChange={applyFilters} />
        </aside>

        <div className="space-y-4">
          {awaitingQuery ? (
            <SearchEmptyPrompt onSearch={(q) => applyFilters({ q })} />
          ) : (
            <>
              <p className="text-sm text-text-tertiary" aria-live="polite">
                {searching ? (
                  "검색 중…"
                ) : (
                  <>
                    <span className="font-medium text-text-secondary">
                      {filtered.length.toLocaleString()}건
                    </span>
                    {filters.q && ` · "${filters.q}"`}
                  </>
                )}
              </p>

              {searching ? (
                <SkeletonGrid count={4} />
              ) : pageItems.length === 0 ? (
                filters.q ? (
                  <NoResultsState
                    query={filters.q}
                    hasFilters={hasExtraFilters}
                    onClear={() => applyFilters({})}
                    onSearch={(q) => applyFilters({ q })}
                  />
                ) : (
                  <div className="ss-card p-8 text-center">
                    <p className="text-text-tertiary">조건에 맞는 항목이 없습니다.</p>
                    {hasExtraFilters && (
                      <button
                        type="button"
                        className="ss-chip ss-chip-active mt-4 touch-target"
                        onClick={() => applyFilters({})}
                      >
                        필터 초기화
                      </button>
                    )}
                  </div>
                )
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {pageItems.map((item, i) => (
                    <NewsCard
                      key={item.id}
                      item={toDigestItem(item, (safePage - 1) * PAGE_SIZE + i + 1)}
                      highlightQuery={filters.q}
                    />
                  ))}
                </div>
              )}

              {!searching && totalPages > 1 && (
                <nav className="flex items-center justify-center gap-2 pt-4" aria-label="페이지">
                  <button
                    type="button"
                    disabled={safePage <= 1}
                    className="ss-chip touch-target disabled:opacity-40"
                    aria-label="이전 페이지"
                    onClick={() => goToPage(safePage - 1)}
                  >
                    ← 이전
                  </button>
                  <span className="text-sm text-text-tertiary" aria-live="polite">
                    {safePage} / {totalPages}
                  </span>
                  <button
                    type="button"
                    disabled={safePage >= totalPages}
                    className="ss-chip touch-target disabled:opacity-40"
                    aria-label="다음 페이지"
                    onClick={() => goToPage(safePage + 1)}
                  >
                    다음 →
                  </button>
                </nav>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
