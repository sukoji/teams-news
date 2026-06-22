import type { Digest, DigestItem } from "./types";
import { SITE_BASE } from "./types";
import { inferTags, inferTopics, sharedTopicReason } from "./topics";

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
  page?: number;
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
  const pageRaw = search.get("page");
  const page = pageRaw ? Math.max(1, parseInt(pageRaw, 10) || 1) : 1;
  return {
    q: search.get("q")?.trim() || undefined,
    source: search.get("source")?.trim() || undefined,
    section: search.get("section")?.trim() || undefined,
    from: search.get("from")?.trim() || undefined,
    to: search.get("to")?.trim() || undefined,
    sort: (search.get("sort") as SortMode) || undefined,
    page,
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
  if (filters.page && filters.page > 1) params.set("page", String(filters.page));
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

const FUSE_KEYS = [
  { name: "t", weight: 0.5 },
  { name: "s", weight: 0.3 },
  { name: "title", weight: 0.4 },
  { name: "summary", weight: 0.2 },
  { name: "matched_keywords", weight: 0.2 },
] as const;

type ArchiveFuse = import("fuse.js").default<SearchIndexItem>;

let fuseModulePromise: Promise<typeof import("fuse.js")> | null = null;
let cachedFuse: ArchiveFuse | null = null;
let cachedFuseItems: SearchIndexItem[] | null = null;

function loadFuseModule() {
  if (!fuseModulePromise) {
    fuseModulePromise = import("fuse.js");
  }
  return fuseModulePromise;
}

/** Memoized fuse instance — recreated only when the items array reference changes. */
export async function getSearchFuse(items: SearchIndexItem[]): Promise<ArchiveFuse> {
  const { default: Fuse } = await loadFuseModule();
  if (cachedFuseItems !== items) {
    cachedFuse = new Fuse(items, {
      keys: [...FUSE_KEYS],
      threshold: 0.4,
      ignoreLocation: true,
    });
    cachedFuseItems = items;
  }
  return cachedFuse!;
}

export function searchWithFuse(fuse: ArchiveFuse, query: string, limit?: number): SearchIndexItem[] {
  const trimmed = query.trim();
  if (!trimmed) return [];
  const results = fuse.search(trimmed, limit != null ? { limit } : undefined);
  return results.map((r) => r.item);
}

export async function searchArchive(
  items: SearchIndexItem[],
  query: string,
): Promise<SearchIndexItem[]> {
  if (!query.trim()) return items;
  const fuse = await getSearchFuse(items);
  return searchWithFuse(fuse, query);
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

export function itemDetailPath(id: string): string {
  return `/item/${id}`;
}

/** Matches outputs/export.py url_hash — stable id from normalized URL. */
export async function urlHash(url: string): Promise<string> {
  const normalized = url.trim().replace(/\/$/, "").toLowerCase();
  const data = new TextEncoder().encode(normalized);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const hex = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, 32);
}

export function sourceToSlug(source: string): string {
  for (const [slug, name] of Object.entries(SOURCE_SLUGS)) {
    if (name === source) return slug;
  }
  return source.toLowerCase().replace(/\s+/g, "-");
}

export function digestItemToSearchIndex(item: DigestItem): SearchIndexItem {
  return {
    id: item.id,
    t: item.title_ko || item.title,
    s: item.summary_ko || item.summary,
    src: sourceToSlug(item.source),
    sec: item.section_id,
    pub: item.published_at,
    col: item.published_at,
    score: item.score,
    pop: item.popularity,
    url: item.url,
    source: item.source,
    section: item.section,
    title: item.title,
    title_ko: item.title_ko,
    summary: item.summary,
    summary_ko: item.summary_ko,
    engagement: item.engagement,
    matched_keywords: item.matched_keywords ?? [],
  };
}

export function findItemByUrl(
  items: SearchIndexItem[],
  url: string,
): SearchIndexItem | undefined {
  return items.find((i) => i.url === url);
}

export function findItemById(
  items: SearchIndexItem[],
  id: string,
): SearchIndexItem | undefined {
  return items.find((i) => i.id === id);
}

export async function resolveItem(
  id: string,
  items: SearchIndexItem[],
  digest: Digest | null,
): Promise<SearchIndexItem | undefined> {
  const byId = findItemById(items, id);
  if (byId) return byId;

  for (const item of items) {
    if ((await urlHash(item.url)) === id) return item;
  }

  if (digest) {
    let digestItem = digest.items.find((d) => d.id === id);
    if (!digestItem) {
      for (const d of digest.items) {
        if ((await urlHash(d.url)) === id) {
          digestItem = d;
          break;
        }
      }
    }

    if (digestItem) {
      const archived = findItemByUrl(items, digestItem.url);
      if (archived) return archived;
      const canonicalId = await urlHash(digestItem.url);
      return digestItemToSearchIndex({ ...digestItem, id: canonicalId });
    }
  }

  return undefined;
}

export interface RelatedItem extends SearchIndexItem {
  /** Korean label explaining why this item is related */
  relatedReason: string;
}

export async function getRelatedItems(
  current: SearchIndexItem,
  allItems: SearchIndexItem[],
  limit = 6,
): Promise<RelatedItem[]> {
  const others = allItems.filter(
    (i) => i.id !== current.id && i.url !== current.url,
  );
  if (others.length === 0) return [];

  const currentTopics = inferTopics(current);
  const currentPrimary = currentTopics[0];
  const currentTopicSet = new Set(currentTopics);
  const currentTags = new Set(inferTags(current));

  const scores = new Map<string, number>();

  for (const item of others) {
    let score = 0;
    const itemTopics = inferTopics(item);
    const itemPrimary = itemTopics[0];

    if (currentPrimary && itemPrimary === currentPrimary) {
      score += 40;
    }
    for (const topicId of itemTopics) {
      if (topicId !== itemPrimary && currentTopicSet.has(topicId)) {
        score += 15;
      }
    }

    for (const tag of inferTags(item)) {
      if (currentTags.has(tag)) score += 5;
    }

    if (item.sec === current.sec) score += 4;

    if (score > 0) scores.set(item.id, score);
  }

  const Fuse = (await import("fuse.js")).default;
  const fuse = new Fuse(others, {
    keys: [
      { name: "t", weight: 0.45 },
      { name: "s", weight: 0.35 },
      { name: "title", weight: 0.4 },
      { name: "summary", weight: 0.25 },
    ],
    threshold: 0.55,
    ignoreLocation: true,
  });
  const query = `${current.t} ${current.s}`.trim();
  for (const result of fuse.search(query, { limit: 30 })) {
    const { item, score: fuseScore = 1 } = result;
    const similarity = Math.max(0, 1 - fuseScore);
    const existing = scores.get(item.id) ?? 0;
    scores.set(item.id, existing + similarity * 5);
  }

  const ranked = [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([id, score]) => ({ item: others.find((i) => i.id === id)!, score }))
    .filter((r) => r.item);

  const minCount = Math.min(limit, Math.max(4, Math.min(6, ranked.length)));
  const picked: RelatedItem[] = [];
  const usedSources = new Set<string>();

  for (const { item, score } of ranked) {
    if (picked.length >= minCount) break;
    const sourcePenalty = usedSources.has(item.src) ? 3 : 0;
    if (picked.length >= 4 && sourcePenalty > 0 && score < 20) continue;
    picked.push({
      ...item,
      relatedReason: sharedTopicReason(current, item) ?? "유사 주제",
    });
    usedSources.add(item.src);
  }

  if (picked.length < minCount) {
    for (const { item } of ranked) {
      if (picked.length >= minCount) break;
      if (picked.some((p) => p.id === item.id)) continue;
      picked.push({
        ...item,
        relatedReason: sharedTopicReason(current, item) ?? "유사 주제",
      });
    }
  }

  return picked.slice(0, limit);
}

export function getMoreFromSource(
  current: SearchIndexItem,
  allItems: SearchIndexItem[],
  limit = 5,
): SearchIndexItem[] {
  return allItems
    .filter((i) => i.id !== current.id && i.src === current.src)
    .sort((a, b) => b.pop - a.pop || b.score - a.score)
    .slice(0, limit);
}
