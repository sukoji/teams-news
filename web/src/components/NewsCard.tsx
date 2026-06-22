import { Link } from "react-router-dom";
import type { DigestItem } from "../lib/types";
import {
  SOURCE_STYLES,
  displaySummary,
  displayTitle,
  formatEngagement,
  formatRelativeTime,
} from "../lib/types";
import { itemDetailPath } from "../lib/archive";
import { highlightText } from "../lib/highlight";
import { Badge } from "../styleseed/components/ui/badge";
import { cn } from "../styleseed/components/ui/utils";

export function NewsCard({
  item,
  highlightQuery,
  compact,
}: {
  item: DigestItem;
  highlightQuery?: string;
  compact?: boolean;
}) {
  const style = SOURCE_STYLES[item.source] ?? { color: "#8a8f98", icon: "📌" };
  const engagement = formatEngagement(item);
  const title = displayTitle(item);
  const summary = displaySummary(item);

  if (compact) {
    return (
      <article
        data-slot="news-card"
        data-variant="compact"
        className="flex flex-col gap-1.5 px-3 py-2.5 transition-colors hover:bg-surface-subtle"
      >
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="secondary"
            className="border-transparent text-[10px] font-semibold uppercase tracking-wide text-white"
            style={{ backgroundColor: style.color }}
          >
            {style.icon} {item.source}
          </Badge>
          <span className="text-[11px] text-text-tertiary">{item.section}</span>
          {engagement && (
            <span className="text-[11px] font-semibold text-brand">{engagement}</span>
          )}
          <time
            dateTime={item.published_at}
            className="ml-auto shrink-0 text-[11px] text-text-disabled"
          >
            {formatRelativeTime(item.published_at)}
          </time>
        </div>
        <h2 className="text-sm font-medium leading-snug text-text-primary">
          <Link
            to={itemDetailPath(item.id)}
            className="line-clamp-2 no-underline hover:text-brand"
          >
            {highlightText(title, highlightQuery)}
          </Link>
        </h2>
      </article>
    );
  }

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
        <Link
          to={itemDetailPath(item.id)}
          className="no-underline hover:text-brand"
        >
          {highlightText(title, highlightQuery)}
        </Link>
      </h2>

      <p className="mb-4 flex-1 text-sm leading-relaxed text-text-tertiary line-clamp-3">
        {highlightText(summary, highlightQuery)}
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
