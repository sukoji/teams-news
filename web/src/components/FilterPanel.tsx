import { useEffect, useState } from "react";
import type { ArchiveMeta, FeedFilters, SortMode } from "../lib/archive";
import { SECTION_LABELS } from "../lib/archive";
import { cn } from "../styleseed/components/ui/utils";

interface FilterPanelProps {
  meta: ArchiveMeta | null;
  filters: FeedFilters;
  onChange: (filters: FeedFilters) => void;
  className?: string;
}

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: "newest", label: "최신순" },
  { value: "popular", label: "인기순" },
  { value: "relevance", label: "관련도" },
];

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "ss-chip touch-target !cursor-pointer whitespace-nowrap !text-xs",
        active && "ss-chip-active",
      )}
    >
      {children}
    </button>
  );
}

export function FilterPanel({ meta, filters, onChange, className }: FilterPanelProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (!drawerOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [drawerOpen]);

  const update = (patch: Partial<FeedFilters>) => {
    onChange({ ...filters, ...patch, page: 1 });
  };

  const panel = (
    <div className="space-y-4">
      <div>
        <p className="ss-section-label mb-2">정렬</p>
        <div className="flex flex-wrap gap-2">
          {SORT_OPTIONS.map((opt) => (
            <Chip
              key={opt.value}
              active={(filters.sort ?? (filters.q ? "relevance" : "newest")) === opt.value}
              onClick={() => update({ sort: opt.value })}
            >
              {opt.label}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <p className="ss-section-label mb-2">섹션</p>
        <div className="flex flex-wrap gap-2">
          <Chip active={!filters.section} onClick={() => update({ section: undefined })}>
            전체
          </Chip>
          {(meta?.sections ?? []).map((sec) => (
            <Chip
              key={sec.id}
              active={filters.section === sec.id}
              onClick={() => update({ section: sec.id })}
            >
              {SECTION_LABELS[sec.id] ?? sec.title} ({sec.count})
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <p className="ss-section-label mb-2">소스</p>
        <div className="flex flex-wrap gap-2">
          <Chip active={!filters.source} onClick={() => update({ source: undefined })}>
            전체
          </Chip>
          {(meta?.sources ?? []).map((src) => (
            <Chip
              key={src.slug}
              active={filters.source === src.slug}
              onClick={() => update({ source: src.slug })}
            >
              {src.name} ({src.count})
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <p className="ss-section-label mb-2">날짜</p>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="date"
            value={filters.from ?? ""}
            onChange={(e) => update({ from: e.target.value || undefined })}
            className="rounded-lg border border-border bg-surface-subtle px-2 py-1.5 text-xs text-text-primary"
          />
          <span className="text-text-disabled">—</span>
          <input
            type="date"
            value={filters.to ?? ""}
            onChange={(e) => update({ to: e.target.value || undefined })}
            className="rounded-lg border border-border bg-surface-subtle px-2 py-1.5 text-xs text-text-primary"
          />
          {(filters.from || filters.to) && (
            <button
              type="button"
              className="ss-chip !text-xs"
              onClick={() => update({ from: undefined, to: undefined })}
            >
              초기화
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className={cn("hidden lg:block", className)}>
        <div className="ss-card p-4">{panel}</div>
      </div>

      <div className="lg:hidden">
        <button
          type="button"
          className="ss-chip ss-chip-active w-full !justify-center"
          onClick={() => setDrawerOpen(true)}
        >
          필터 · 정렬
        </button>
        {drawerOpen && (
          <div
            className="fixed inset-0 z-[60] flex flex-col bg-surface-page/95 backdrop-blur-sm"
            role="dialog"
            aria-modal="true"
            aria-label="필터"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <span className="font-semibold text-text-primary">필터</span>
              <button type="button" className="ss-chip" onClick={() => setDrawerOpen(false)}>
                닫기
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">{panel}</div>
            <div className="border-t border-border p-4">
              <button
                type="button"
                className="ss-chip ss-chip-active w-full !justify-center"
                onClick={() => setDrawerOpen(false)}
              >
                적용
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
