const RECENT_KEY = "teams-news-recent-searches";
const MAX_RECENT = 8;

export function loadRecentSearches(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function saveRecentSearch(query: string): void {
  const trimmed = query.trim();
  if (!trimmed) return;
  const next = [trimmed, ...loadRecentSearches().filter((q) => q !== trimmed)].slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}

export const SEARCH_SUGGESTIONS = ["LLM", "RAG", "Agent", "PyTorch", "Hugging Face"] as const;
