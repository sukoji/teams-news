import type { DigestItem } from "../lib/types";
import {
  SOURCE_STYLES,
  displaySummary,
  displayTitle,
  formatEngagement,
  formatRelativeTime,
} from "../lib/types";
import { Badge } from "../styleseed/components/ui/badge";
import { cn } from "../styleseed/components/ui/utils";

export function NewsCard({ item }: { item: DigestItem }) {
  const style = SOURCE_STYLES[item.source] ?? { color: "#8a8f98", icon: "📌" };
  const engagement = formatEngagement(item);

  return (
    <article
      data-slot="news-card"
      className={cn(
        "ss-card flex h-full flex-col p-4 sm:p-5",
      )}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge
          variant="secondary"
          className="border-transparent text-[11px] font-semibold uppercase tracking-wide text-white"
          style={{ backgroundColor: style.color }}
        >
          {style.icon} {item.source}
        </Badge>
        <span className="text-xs text-text-tertiary">{item.section}</span>
        {engagement && (
          <span className="ml-auto text-xs font-semibold text-brand">{engagement}</span>
        )}
      </div>

      <h2 className="mb-2 text-base font-semibold leading-snug tracking-tight text-text-primary sm:text-lg">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="no-underline hover:text-brand"
        >
          {displayTitle(item)}
        </a>
      </h2>

      <p className="mb-4 flex-1 text-sm leading-relaxed text-text-tertiary line-clamp-3">
        {displaySummary(item)}
      </p>

      <div className="flex items-center justify-between gap-2 border-t border-border pt-3 text-xs text-text-disabled">
        <time dateTime={item.published_at}>{formatRelativeTime(item.published_at)}</time>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-brand no-underline hover:underline"
        >
          원문 →
        </a>
      </div>
    </article>
  );
}
