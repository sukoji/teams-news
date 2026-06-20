import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { cn } from "../styleseed/components/ui/utils";

const RECENT_KEY = "teams-news-recent-searches";
const MAX_RECENT = 8;

interface SearchBarProps {
  className?: string;
  compact?: boolean;
}

function loadRecent(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function saveRecent(query: string) {
  const trimmed = query.trim();
  if (!trimmed) return;
  const next = [trimmed, ...loadRecent().filter((q) => q !== trimmed)].slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}

export function SearchBar({ className, compact }: SearchBarProps) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [recent, setRecent] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const q = params.get("q") ?? "";
  const searchPath = location.pathname.includes("/feed") ? "/feed" : "/search";

  useEffect(() => {
    setRecent(loadRecent());
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && !isInputFocused()) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = (value: string) => {
    const next = new URLSearchParams(params);
    const trimmed = value.trim();
    if (trimmed) {
      next.set("q", trimmed);
      saveRecent(trimmed);
      setRecent(loadRecent());
    } else {
      next.delete("q");
    }
    next.delete("page");
    setOpen(false);
    navigate(`${searchPath}?${next.toString()}`);
  };

  return (
    <div className={cn("relative flex-1", className)}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(inputRef.current?.value ?? "");
        }}
      >
        <input
          ref={inputRef}
          type="search"
          name="q"
          defaultValue={q}
          placeholder={compact ? "검색… (/)" : "제목·요약 검색 — LLM, RAG, Agent… ( / )"}
          className={cn(
            "w-full rounded-lg border border-border bg-surface-subtle px-3 py-2 text-sm text-text-primary",
            "placeholder:text-text-disabled focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30",
            compact ? "py-1.5 touch-target" : "sm:px-4 sm:py-2.5",
          )}
          aria-label="아카이브 검색"
          aria-expanded={open && recent.length > 0}
          aria-controls="recent-searches"
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {!compact && (
          <kbd className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-surface-page px-1.5 py-0.5 text-[10px] text-text-disabled sm:inline">
            /
          </kbd>
        )}
      </form>

      {open && recent.length > 0 && !q && (
        <ul
          id="recent-searches"
          className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-lg border border-border bg-surface-page shadow-lg"
          role="listbox"
          aria-label="최근 검색"
        >
          <li className="border-b border-border px-3 py-1.5 text-[10px] font-medium uppercase tracking-wide text-text-disabled">
            최근 검색
          </li>
          {recent.map((term) => (
            <li key={term} role="option">
              <button
                type="button"
                className="w-full px-3 py-2 text-left text-sm text-text-secondary hover:bg-surface-subtle touch-target"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  if (inputRef.current) inputRef.current.value = term;
                  submit(term);
                }}
              >
                {term}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  return tag === "input" || tag === "textarea" || (el as HTMLElement).isContentEditable;
}
