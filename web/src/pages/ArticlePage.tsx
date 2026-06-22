import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { RelatedNewsCard } from "../components/RelatedNewsCard";
import { usePageMeta } from "../hooks/usePageMeta";
import {
  resolveItem,
  fetchSearchIndex,
  getMoreFromSource,
  getRelatedItems,
  itemDetailPath,
  toDigestItem,
} from "../lib/archive";
import type { SearchIndexItem } from "../lib/archive";
import {
  SITE_BASE,
  SOURCE_STYLES,
  displaySummary,
  displayTitle,
  fetchDigest,
  formatEngagement,
  formatRelativeTime,
} from "../lib/types";
import { Badge } from "../styleseed/components/ui/badge";
import { cn } from "../styleseed/components/ui/utils";

function geekNewsCommentsUrl(url: string): string | null {
  if (!url.includes("news.hada.io/topic")) return null;
  return url.includes("#") ? url : `${url}#comments`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ArticlePage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState<SearchIndexItem | null>(null);
  const [related, setRelated] = useState<SearchIndexItem[]>([]);
  const [fromSource, setFromSource] = useState<SearchIndexItem[]>([]);
  const [inDigest, setInDigest] = useState<{ date: string; index: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [shareLabel, setShareLabel] = useState("링크 복사");

  const digestItem = item ? toDigestItem(item, 0) : null;
  const title = digestItem ? displayTitle(digestItem) : "";
  const summary = digestItem ? displaySummary(digestItem) : "";
  const detailUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}${SITE_BASE}${itemDetailPath(id)}`
      : `${SITE_BASE}${itemDetailPath(id)}`;

  usePageMeta({
    title: title || "기사",
    description: summary.slice(0, 160) || undefined,
    url: item ? detailUrl : undefined,
  });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setNotFound(false);

    Promise.all([fetchSearchIndex(), fetchDigest().catch(() => null)])
      .then(async ([index, digest]) => {
        if (cancelled) return;
        const found = await resolveItem(id, index.items, digest);
        if (!found) {
          setNotFound(true);
          setItem(null);
          return;
        }
        setItem(found);
        const [rel, more] = await Promise.all([
          getRelatedItems(found, index.items),
          Promise.resolve(getMoreFromSource(found, index.items)),
        ]);
        if (cancelled) return;
        setRelated(rel);
        setFromSource(more);

        if (digest) {
          const match =
            digest.items.find((d) => d.id === found.id) ??
            digest.items.find((d) => d.url === found.url);
          if (match) {
            setInDigest({ date: digest.date, index: match.index });
          }
        }
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleShare = useCallback(async () => {
    const url = `${window.location.origin}${SITE_BASE}${itemDetailPath(id)}`;
    try {
      if (navigator.share) {
        await navigator.share({ title, url, text: summary.slice(0, 100) });
        return;
      }
      await navigator.clipboard.writeText(url);
      setShareLabel("복사됨!");
      setTimeout(() => setShareLabel("링크 복사"), 2000);
    } catch {
      /* user cancelled share */
    }
  }, [id, title, summary]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="h-4 w-48 animate-pulse rounded bg-surface-subtle" />
        <div className="ss-card h-64 animate-pulse bg-surface-subtle" />
      </div>
    );
  }

  if (notFound || !item || !digestItem) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="ss-card p-8 text-center">
          <p className="mb-2 font-medium text-text-primary">기사를 찾을 수 없습니다</p>
          <p className="mb-4 text-sm text-text-tertiary">
            아카이브에 없거나 ID가 잘못되었을 수 있습니다.
          </p>
          <Link to="/feed" className="ss-chip ss-chip-active no-underline">
            피드로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  const style = SOURCE_STYLES[item.source] ?? { color: "#8a8f98", icon: "📌" };
  const engagement = formatEngagement(digestItem);
  const commentsUrl = item.source === "GeekNews" ? geekNewsCommentsUrl(item.url) : null;

  return (
    <div className="space-y-8">
      <nav aria-label="breadcrumb" className="text-sm text-text-tertiary">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li>
            <Link to="/" className="text-brand no-underline hover:underline">
              홈
            </Link>
          </li>
          <li aria-hidden>/</li>
          <li>
            <Link to="/feed" className="text-brand no-underline hover:underline">
              피드
            </Link>
          </li>
          <li aria-hidden>/</li>
          <li>
            <Link
              to={`/section/${item.sec}`}
              className="text-brand no-underline hover:underline"
            >
              {item.section}
            </Link>
          </li>
        </ol>
      </nav>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_260px]">
        <div className="min-w-0 space-y-8">
          <article className="ss-card mx-auto max-w-3xl p-6 sm:p-10">
            <div className="mb-6 flex flex-wrap items-center gap-2">
              <Badge
                variant="secondary"
                className="border-transparent text-[11px] font-semibold uppercase tracking-wide text-white"
                style={{ backgroundColor: style.color }}
              >
                {style.icon} {item.source}
              </Badge>
              <Link
                to={`/section/${item.sec}`}
                className="text-xs text-text-tertiary no-underline hover:text-brand"
              >
                {item.section}
              </Link>
              {engagement && (
                <span className="ml-auto text-sm font-semibold text-brand">{engagement}</span>
              )}
            </div>

            <h1 className="mb-4 text-2xl font-bold leading-tight tracking-tight text-text-primary sm:text-3xl">
              {title}
            </h1>

            {digestItem.title_ko && digestItem.title !== digestItem.title_ko && (
              <p className="mb-4 text-base text-text-secondary">{digestItem.title}</p>
            )}

            <div className="mb-6 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-text-tertiary">
              <time dateTime={item.pub}>{formatDate(item.pub)}</time>
              <span aria-hidden>·</span>
              <span>{formatRelativeTime(item.pub)}</span>
              {inDigest && (
                <>
                  <span aria-hidden>·</span>
                  <Link
                    to={`/date/${inDigest.date}`}
                    className="rounded-full bg-brand-tint px-2.5 py-0.5 text-xs font-semibold text-brand no-underline hover:underline"
                  >
                    {inDigest.date} Top 7 #{inDigest.index}
                  </Link>
                </>
              )}
            </div>

            <div className="prose prose-sm mb-8 max-w-none">
              <p className="text-base leading-relaxed text-text-secondary sm:text-lg sm:leading-relaxed">
                {summary}
              </p>
            </div>

            {item.matched_keywords.length > 0 && (
              <div className="mb-6 flex flex-wrap gap-2">
                {item.matched_keywords.map((kw) => (
                  <Link
                    key={kw}
                    to={`/search?q=${encodeURIComponent(kw)}`}
                    className="ss-chip text-xs no-underline"
                  >
                    {kw}
                  </Link>
                ))}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 border-t border-border pt-6">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ss-chip ss-chip-active touch-target no-underline"
              >
                원문 보기 →
              </a>
              {commentsUrl && (
                <a
                  href={commentsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ss-chip touch-target no-underline"
                >
                  GeekNews 댓글 →
                </a>
              )}
              <button
                type="button"
                onClick={handleShare}
                className="ss-chip touch-target"
                aria-label="기사 링크 공유"
              >
                {shareLabel}
              </button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className={cn("ss-chip touch-target ml-auto")}
              >
                ← 뒤로
              </button>
            </div>
          </article>

          {related.length > 0 && (
            <section aria-labelledby="related-heading">
              <h2
                id="related-heading"
                className="mb-4 text-lg font-semibold text-text-primary"
              >
                함께 보면 좋을 뉴스
              </h2>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {related.map((rel) => (
                  <RelatedNewsCard key={rel.id} item={rel} />
                ))}
              </div>
            </section>
          )}
        </div>

        {fromSource.length > 0 && (
          <aside aria-labelledby="source-more-heading" className="space-y-4">
            <h2
              id="source-more-heading"
              className="text-sm font-semibold text-text-primary"
            >
              {item.source} 더보기
            </h2>
            <ul className="space-y-2">
              {fromSource.map((srcItem) => (
                <li key={srcItem.id}>
                  <Link
                    to={itemDetailPath(srcItem.id)}
                    className="block rounded-lg border border-border p-3 text-sm no-underline transition-colors hover:border-brand/40 hover:bg-surface-subtle"
                  >
                    <span className="line-clamp-2 font-medium text-text-primary">
                      {displayTitle(toDigestItem(srcItem, 0))}
                    </span>
                    <span className="mt-1 block text-xs text-text-disabled">
                      {formatRelativeTime(srcItem.pub)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
            <Link
              to={`/source/${item.src}`}
              className="text-sm font-medium text-brand no-underline hover:underline"
            >
              {item.source} 전체 →
            </Link>
          </aside>
        )}
      </div>
    </div>
  );
}
