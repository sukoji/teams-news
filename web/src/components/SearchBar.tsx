import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { cn } from "../styleseed/components/ui/utils";

interface SearchBarProps {
  className?: string;
  compact?: boolean;
}

export function SearchBar({ className, compact }: SearchBarProps) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const q = params.get("q") ?? "";
  const searchPath = location.pathname.includes("/feed") ? "/feed" : "/search";

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && !isInputFocused()) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = (value: string) => {
    const next = new URLSearchParams(params);
    const trimmed = value.trim();
    if (trimmed) next.set("q", trimmed);
    else next.delete("q");
    navigate(`${searchPath}?${next.toString()}`);
  };

  return (
    <form
      className={cn("relative flex-1", className)}
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
          "placeholder:text-text-disabled focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand",
          compact ? "py-1.5" : "sm:px-4 sm:py-2.5",
        )}
        aria-label="Search archive"
      />
      {!compact && (
        <kbd className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-surface-page px-1.5 py-0.5 text-[10px] text-text-disabled sm:inline">
          /
        </kbd>
      )}
    </form>
  );
}

function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  return tag === "input" || tag === "textarea" || (el as HTMLElement).isContentEditable;
}
