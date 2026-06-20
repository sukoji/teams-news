export function SkeletonCard() {
  return (
    <div className="ss-card flex h-full flex-col p-4 sm:p-5" aria-hidden>
      <div className="mb-3 flex gap-2">
        <div className="h-5 w-24 animate-pulse rounded-full bg-surface-subtle" />
        <div className="h-5 w-16 animate-pulse rounded-full bg-surface-subtle" />
      </div>
      <div className="mb-2 h-6 w-full animate-pulse rounded bg-surface-subtle" />
      <div className="mb-2 h-6 w-4/5 animate-pulse rounded bg-surface-subtle" />
      <div className="mb-4 flex-1 space-y-2">
        <div className="h-4 w-full animate-pulse rounded bg-surface-subtle" />
        <div className="h-4 w-full animate-pulse rounded bg-surface-subtle" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-surface-subtle" />
      </div>
      <div className="flex justify-between border-t border-border pt-3">
        <div className="h-4 w-16 animate-pulse rounded bg-surface-subtle" />
        <div className="h-4 w-12 animate-pulse rounded bg-surface-subtle" />
      </div>
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2" aria-busy="true" aria-label="로딩 중">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
