export interface Engagement {
  label: string;
  value: number;
}

export interface DigestItem {
  id: string;
  index: number;
  title: string;
  title_ko: string | null;
  summary: string;
  summary_ko: string | null;
  url: string;
  source: string;
  section: string;
  section_id: string;
  published_at: string;
  popularity: number;
  upvotes: number;
  score: number;
  importance_score: number;
  matched_keywords: string[];
  engagement: Engagement | null;
}

export interface DigestSection {
  id: string;
  title: string;
  items: DigestItem[];
}

export interface Digest {
  schema_version: number;
  date: string;
  generated_at: string;
  title: string;
  item_count: number;
  sections: DigestSection[];
  items: DigestItem[];
}

export const SITE_BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

export const FEED_URLS = {
  all: `${SITE_BASE}/feed.xml`,
  daily: `${SITE_BASE}/feed/daily.xml`,
  full: `${SITE_BASE}/feed/full.xml`,
  papers: `${SITE_BASE}/feed/papers.xml`,
  news: `${SITE_BASE}/feed/news.xml`,
  trending: `${SITE_BASE}/feed/trending.xml`,
  community: `${SITE_BASE}/feed/community.xml`,
  json: `${SITE_BASE}/data/latest.json`,
  catalog: `${SITE_BASE}/data/feeds.json`,
  archive: `${SITE_BASE}/data/archive/search-index.json`,
} as const;

export const SOURCE_STYLES: Record<string, { color: string; icon: string }> = {
  GeekNews: { color: "#6366f1", icon: "📰" },
  "AI Times": { color: "#0ea5e9", icon: "📰" },
  "Hugging Face Papers": { color: "#f59e0b", icon: "📄" },
  "Elvis AI Newsletter": { color: "#ff6719", icon: "📄" },
  "PyTorch Korea": { color: "#ee4c2c", icon: "💬" },
  "GitHub Trending": { color: "#8b5cf6", icon: "🔥" },
  "전자신문 IT": { color: "#10b981", icon: "📰" },
  "NAVER D2": { color: "#22c55e", icon: "📰" },
  "ZDNet Korea": { color: "#3b82f6", icon: "📰" },
};

export function displayTitle(item: DigestItem): string {
  return item.title_ko || item.title;
}

export function displaySummary(item: DigestItem): string {
  return item.summary_ko || item.summary;
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "방금";
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}일 전`;
  return date.toLocaleDateString("ko-KR", { month: "short", day: "numeric" });
}

export function formatEngagement(item: DigestItem): string | null {
  if (!item.engagement) return null;
  const { label, value } = item.engagement;
  const formatted = typeof value === "number" ? value.toLocaleString() : value;
  return `${label} ${formatted}`;
}

export async function fetchDigest(path = `${SITE_BASE}/data/latest.json`): Promise<Digest> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load digest: ${res.status}`);
  return res.json() as Promise<Digest>;
}

export async function fetchArchiveDates(): Promise<string[]> {
  const manifestPath = `${SITE_BASE}/data/archive-index.json`;
  try {
    const res = await fetch(manifestPath);
    if (res.ok) {
      const data = (await res.json()) as { dates: string[] };
      return data.dates.sort().reverse();
    }
  } catch {
    /* fallback below */
  }
  return [];
}

export interface ArchiveIndexManifest {
  dates: string[];
  digest_counts?: Record<string, number>;
  archive_counts?: Record<string, number>;
}
