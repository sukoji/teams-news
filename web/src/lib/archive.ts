import type { DigestItem } from "./types";
import { SITE_BASE } from "./types";

export interface ArchiveMeta {
  schema_version: number;
  generated_at: string;
  total: number;
  sources: { slug: string; name: string; count: number }[];
  sections: { id: string; title: string; count: number }[];
  date_counts: Record<string, number>;
}

export interface SearchIndexItem {
  id: string;
  t: string;
  s: string;
  src: string;
  sec: string;
  pub: string;
  col: string;
  score: number;
  pop: number;
  url: string;
  source: string;
  section: string;
  title: string;
  title_ko: string | null;
  summary: string;
  summary_ko: string | null;
  engagement: { label: string; value: number } | null;
  matched_keywords: string[];
}

export interface SearchIndex {
  schema_version: number;
  generated_at: string;
  total: number;
  sources: ArchiveMeta["sources"];
  sections: ArchiveMeta["sections"];
  date_counts: Record<string, number>;
  items: SearchIndexItem[];
}

export interface ArchiveIndex {
  dates: string[];
  digest_counts?: Record<string, number>;
  archive_counts?: Record<string, number>;
}

export type SortMode = "newest" | "popular" | "relevance";

export interface FeedFilters {
  q?: string;
  source?: string;
  section?: string;
  from?: string;
  to?: string;
  sort?: SortMode;
}

const META_URL = `${SITE_BASE}/data/archive/meta.json`;
const INDEX_URL = `${SITE_BASE}/data/archive/search-index.json`;

let cachedIndex: SearchIndex | null = null;
let cachedMeta: ArchiveMeta | null = null;

export async function fetchArchiveMeta(): Promise<ArchiveMeta> {
  if (cachedMeta) return cachedMeta;
  const res = await fetch(META_URL);
  if (!res.ok) throw new Error(`Failed to load archive meta: ${res.status}`);
  cachedMeta = (await res.json()) as ArchiveMeta;
  return cachedMeta;
}

export async function fetchSearchIndex(): Promise<SearchIndex> {
  if (cachedIndex) return cachedIndex;
  const res = await fetch(INDEX_URL);
  if (!res.ok) throw new Error(`Failed to load search index: ${res.status}`);
  cachedIndex = (await res.json()) as SearchIndex;
  return cachedIndex;
}

export function toDigestItem(item: SearchIndexItem, index: number): DigestItem {
  return {
    id: item.id,
    index,
    title: item.title,
    title_ko: item.title_ko,
    summary: item.summary,
    summary_ko: item.summary_ko,
    url: item.url,
    source: item.source,
    section: item.section,
    section_id: item.sec,
    published_at: item.pub,
    popularity: item.pop,
    upvotes: 0,
    score: item.score,
    importance_score: item.score,
    matched_keywords: item.matched_keywords ?? [],
    engagement: item.engagement,
  };
}

export function parseFilters(search: URLSearchParams): FeedFilters {
  return {
    q: search.get("q")?.trim() || undefined,
    source: search.get("source")?.trim() || undefined,
    section: search.get("section")?.trim() || undefined,
    from: search.get("from")?.trim() || undefined,
    to: search.get("to")?.trim() || undefined,
    sort: (search.get("sort") as SortMode) || undefined,
  };
}

export function filtersToSearchParams(filters: FeedFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.source) params.set("source", filters.source);
  if (filters.section) params.set("section", filters.section);
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.sort && filters.sort !== "newest") params.set("sort", filters.sort);
  return params;
}

function inDateRange(iso: string, from?: string, to?: string): boolean {
  const day = iso.slice(0, 10);
  if (from && day < from) return false;
  if (to && day > to) return false;
  return true;
}

export function filterItems(
  items: SearchIndexItem[],
  filters: FeedFilters,
  fuseResults?: SearchIndexItem[],
): SearchIndexItem[] {
  let result = fuseResults ?? items;

  if (filters.source) {
    result = result.filter((i) => i.src === filters.source);
  }
  if (filters.section) {
    result = result.filter((i) => i.sec === filters.section);
  }
  if (filters.from || filters.to) {
    result = result.filter((i) => inDateRange(i.pub, filters.from, filters.to));
  }

  const sort = filters.sort ?? (filters.q ? "relevance" : "newest");
  if (sort === "newest") {
    result = [...result].sort((a, b) => b.col.localeCompare(a.col));
  } else if (sort === "popular") {
    result = [...result].sort((a, b) => b.pop - a.pop || b.score - a.score);
  }
  // relevance: keep fuse order when q is set

  return result;
}

export async function searchArchive(
  items: SearchIndexItem[],
  query: string,
): Promise<SearchIndexItem[]> {
  if (!query.trim()) return items;
  const Fuse = (await import("fuse.js")).default;
  const fuse = new Fuse(items, {
    keys: [
      { name: "t", weight: 0.5 },
      { name: "s", weight: 0.3 },
      { name: "title", weight: 0.4 },
      { name: "summary", weight: 0.2 },
      { name: "matched_keywords", weight: 0.2 },
    ],
    threshold: 0.4,
    ignoreLocation: true,
  });
  return fuse.search(query).map((r) => r.item);
}

export const PAGE_SIZE = 24;

export function paginate<T>(items: T[], page: number, pageSize = PAGE_SIZE): T[] {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

export const SOURCE_SLUGS: Record<string, string> = {
  geeknews: "GeekNews",
  aitimes: "AI Times",
  huggingface: "Hugging Face Papers",
  "pytorch-korea": "PyTorch Korea",
  "github-trending": "GitHub Trending",
  etnews: "전자신문 IT",
  "naver-d2": "NAVER D2",
  "zdnet-korea": "ZDNet Korea",
};

export const SECTION_LABELS: Record<string, string> = {
  papers: "📄 Papers",
  news: "📰 News",
  trending: "🔥 Trending",
  community: "💬 Community",
  other: "📌 기타",
};
