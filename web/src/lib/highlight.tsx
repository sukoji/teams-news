import type { ReactNode } from "react";

function escapeRegex(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Split text into segments with query terms wrapped in <mark>. */
export function highlightText(text: string, query?: string): ReactNode {
  if (!query?.trim()) return text;

  const terms = query
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map(escapeRegex);

  if (!terms.length) return text;

  const pattern = new RegExp(`(${terms.join("|")})`, "gi");
  const parts = text.split(pattern);
  const lowerTerms = new Set(terms.map((t) => t.toLowerCase()));

  return parts.map((part, i) =>
    lowerTerms.has(part.toLowerCase()) ? (
      <mark key={i} className="rounded bg-brand-tint px-0.5 text-inherit">
        {part}
      </mark>
    ) : (
      part
    ),
  );
}
