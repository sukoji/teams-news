const SECTIONS = [
  { id: "all", label: "전체" },
  { id: "papers", label: "📄 Papers" },
  { id: "news", label: "📰 News" },
  { id: "trending", label: "🔥 Trending" },
  { id: "community", label: "💬 Community" },
] as const;

export type SectionFilter = (typeof SECTIONS)[number]["id"];

interface SectionChipsProps {
  active: SectionFilter;
  onChange: (id: SectionFilter) => void;
  counts: Record<string, number>;
}

export function SectionChips({ active, onChange, counts }: SectionChipsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {SECTIONS.map(({ id, label }) => {
        const count = id === "all" ? counts.all : counts[id] ?? 0;
        const isActive = active === id;
        return (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            className={`ss-chip ${isActive ? "ss-chip-active" : ""}`}
          >
            {label}
            <span className="opacity-70">{count}</span>
          </button>
        );
      })}
    </div>
  );
}

export { SECTIONS };
