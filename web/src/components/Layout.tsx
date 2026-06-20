import { Link, NavLink } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";
import { SITE_BASE } from "../lib/types";
import { cn } from "../styleseed/components/ui/utils";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "text-sm font-medium transition-colors duration-[var(--duration-normal)]",
    isActive ? "text-brand" : "text-text-tertiary hover:text-text-primary",
  );

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggle } = useTheme();

  return (
    <div className="flex min-h-screen flex-col bg-surface-page">
      <header className="sticky top-0 z-50 border-b border-border bg-[color-mix(in_srgb,var(--surface-page)_88%,transparent)] backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2 no-underline">
            <span className="text-lg font-semibold tracking-tight text-text-primary">
              PIAI Teams News
            </span>
          </Link>
          <nav className="flex items-center gap-4 sm:gap-6">
            <NavLink to="/" end className={navLinkClass}>
              오늘
            </NavLink>
            <NavLink to="/archive" className={navLinkClass}>
              아카이브
            </NavLink>
            <NavLink to="/subscribe" className={navLinkClass}>
              RSS
            </NavLink>
            <NavLink to="/about" className={navLinkClass}>
              About
            </NavLink>
            <button
              type="button"
              onClick={toggle}
              className="ss-chip touch-target !cursor-pointer !py-1.5"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 text-sm text-text-tertiary sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <span>
            Powered by{" "}
            <a
              href="https://piai.postech.ac.kr"
              className="text-brand no-underline hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              PIAI
            </a>
          </span>
          <a
            href="https://github.com/jskh-201910840/teams-news"
            className="text-brand no-underline hover:underline"
            target="_blank"
            rel="noreferrer"
          >
            GitHub — jskh-201910840/teams-news
          </a>
          <span className="text-xs">JSON API: {SITE_BASE}/data/latest.json</span>
        </div>
      </footer>
    </div>
  );
}
