import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { fetchSearchIndex, getSearchFuse, searchWithFuse, toDigestItem } from "../lib/archive";
import type { SearchIndexItem } from "../lib/archive";
import { loadRecentSearches, saveRecentSearch } from "../lib/recentSearches";
import { cn } from "../styleseed/components/ui/utils";
import { NewsCard } from "./NewsCard";

const DEBOUNCE_MS = 200;
const PREVIEW_LIMIT = 8;

interface SearchBarProps {
  className?: string;
  compact?: boolean;
}

export function SearchBar({ className, compact }: SearchBarProps) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const urlQ = params.get("q") ?? "";
  const [inputValue, setInputValue] = useState(urlQ);
  const debouncedQ = useDebouncedValue(inputValue, DEBOUNCE_MS);
  const [recent, setRecent] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const [previewItems, setPreviewItems] = useState<SearchIndexItem[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);

  const searchPath = location.pathname.includes("/feed") ? "/feed" : "/search";

  useEffect(() => {
    setRecent(loadRecentSearches());
  }, []);

  useEffect(() => {
    setInputValue(urlQ);
  }, [urlQ]);

  const syncUrl = useCallback(
    (query: string, replace = true) => {
      const trimmed = query.trim();
      const next = new URLSearchParams(params);
      if (trimmed) next.set("q", trimmed);
      else next.delete("q");
      next.delete("page");

      let targetPath = searchPath;
      if (trimmed && location.pathname === "/") {
        targetPath = "/search";
      }

      const nextQ = next.get("q") ?? "";
      if (nextQ === urlQ && targetPath === location.pathname) return;

      navigate(`${targetPath}?${next.toString()}`, { replace });
    },
    [navigate, params, searchPath, location.pathname, urlQ],
  );

  useEffect(() => {
    syncUrl(debouncedQ, true);
  }, [debouncedQ, syncUrl]);

  useEffect(() => {
    if (!compact || !debouncedQ.trim()) {
      setPreviewItems([]);
      setPreviewLoading(false);
      return;
    }

    let cancelled = false;
    setPreviewLoading(true);

    (async () => {
      try {
        const index = await fetchSearchIndex();
        if (cancelled) return;
        const fuse = await getSearchFuse(index.items);
        if (cancelled) return;
        setPreviewItems(searchWithFuse(fuse, debouncedQ, PREVIEW_LIMIT));
      } catch {
        if (!cancelled) setPreviewItems([]);
      } finally {
        if (!cancelled) setPreviewLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [compact, debouncedQ]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && !isInputFocused()) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = (value: string) => {
    const trimmed = value.trim();
    if (trimmed) {
      saveRecentSearch(trimmed);
      setRecent(loadRecentSearches());
    }
    setOpen(false);
    syncUrl(trimmed, false);
  };

  const showRecent = open && !inputValue.trim() && recent.length > 0;
  const showPreview =
    compact && open && !!debouncedQ.trim() && (previewLoading || previewItems.length > 0);
  const showDropdown = showRecent || showPreview;

  return (
    <div className={cn("relative flex-1", className)}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(inputValue);
        }}
      >
        <input
          ref={inputRef}
          type="search"
          name="q"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={compact ? "검색… (/)" : "제목·요약 검색 — LLM, RAG, Agent… ( / )"}
          className={cn(
            "w-full rounded-lg border border-border bg-surface-subtle px-3 py-2 text-sm text-text-primary",
            "placeholder:text-text-disabled focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30",
            compact ? "py-1.5 touch-target" : "sm:px-4 sm:py-2.5",
          )}
          aria-label="아카이브 검색"
          aria-expanded={showDropdown}
          aria-controls="search-dropdown"
          aria-autocomplete="list"
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {!compact && (
          <kbd className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-surface-page px-1.5 py-0.5 text-[10px] text-text-disabled sm:inline">
            /
          </kbd>
        )}
      </form>

      {showDropdown && (
        <div
          id="search-dropdown"
          className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-lg border border-border bg-surface-page shadow-lg ring-1 ring-black/5"
          aria-label={showPreview ? "검색 미리보기" : "최근 검색"}
        >
          {showRecent && (
            <ul>
              <li className="border-b border-border px-3 py-1.5 text-[10px] font-medium uppercase tracking-wide text-text-disabled">
                최근 검색
              </li>
              {recent.map((term) => (
                <li key={term} role="option">
                  <button
                    type="button"
                    className="w-full px-3 py-2 text-left text-sm text-text-secondary hover:bg-surface-subtle touch-target"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      setInputValue(term);
                      submit(term);
                    }}
                  >
                    {term}
                  </button>
                </li>
              ))}
            </ul>
          )}

          {showPreview && (
            <div>
              <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
                <span className="text-[10px] font-medium uppercase tracking-wide text-text-disabled">
                  미리보기
                </span>
                <Link
                  to={`/search?q=${encodeURIComponent(debouncedQ.trim())}`}
                  className="text-[10px] font-medium text-brand no-underline hover:underline"
                  onMouseDown={(e) => e.preventDefault()}
                >
                  전체 보기 →
                </Link>
              </div>
              <div
                className="max-h-[min(70vh,32rem)] overflow-y-auto overscroll-contain divide-y divide-border"
                role="listbox"
                aria-label="검색 결과 미리보기"
              >
                {previewLoading ? (
                  Array.from({ length: 4 }, (_, i) => (
                    <div key={i} className="px-3 py-2.5" aria-hidden>
                      <div className="mb-2 flex gap-2">
                        <div className="h-4 w-16 animate-pulse rounded-full bg-surface-subtle" />
                        <div className="h-4 w-12 animate-pulse rounded-full bg-surface-subtle" />
                      </div>
                      <div className="h-4 w-full animate-pulse rounded bg-surface-subtle" />
                      <div className="mt-1 h-4 w-4/5 animate-pulse rounded bg-surface-subtle" />
                    </div>
                  ))
                ) : (
                  previewItems.map((item, i) => (
                    <div key={item.id} role="option" onMouseDown={(e) => e.preventDefault()}>
                      <NewsCard
                        item={toDigestItem(item, i + 1)}
                        highlightQuery={debouncedQ}
                        compact
                      />
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  return tag === "input" || tag === "textarea" || (el as HTMLElement).isContentEditable;
}
