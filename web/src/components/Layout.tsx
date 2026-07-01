import { Link, NavLink } from "react-router-dom";
import { SearchBar } from "./SearchBar";
import { useTheme } from "../hooks/useTheme";
import { SITE_BASE } from "../lib/types";
import { cn } from "../styleseed/components/ui/utils";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "text-sm font-medium transition-colors duration-[var(--duration-normal)] touch-target inline-flex items-center whitespace-nowrap",
    isActive ? "text-brand" : "text-text-tertiary hover:text-text-primary",
  );

const FOOTER_LINKS = [
  { to: "/", label: "오늘" },
  { to: "/feed", label: "피드" },
  { to: "/search", label: "검색" },
  { to: "/archive", label: "아카이브" },
  { to: "/subscribe", label: "RSS" },
  { to: "/about", label: "About" },
] as const;

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggle } = useTheme();

  return (
    <div className="flex min-h-screen flex-col bg-surface-page">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2 focus:text-white"
      >
        본문으로 건너뛰기
      </a>

      <header className="sticky top-0 z-50 overflow-visible border-b border-border bg-[color-mix(in_srgb,var(--surface-page)_88%,transparent)] backdrop-blur-md">
        <div className="relative mx-auto flex max-w-6xl flex-col gap-3 overflow-visible px-4 py-3 sm:px-6">
          <div className="relative z-20 flex items-center justify-between gap-4">
            <Link to="/" className="flex shrink-0 items-center gap-2 no-underline">
              <span className="text-lg font-semibold tracking-tight text-text-primary">
                PIAI Teams News
              </span>
            </Link>
            <nav
              className="relative z-20 scrollbar-hide flex items-center gap-1 overflow-x-auto sm:gap-3"
              aria-label="주요 메뉴"
            >
              <NavLink to="/" end className={navLinkClass}>
                오늘
              </NavLink>
              <NavLink to="/feed" className={navLinkClass}>
                피드
              </NavLink>
              <NavLink to="/search" className={navLinkClass}>
                검색
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
                aria-label={theme === "dark" ? "라이트 모드로 전환" : "다크 모드로 전환"}
              >
                {theme === "dark" ? "☀️" : "🌙"}
              </button>
            </nav>
          </div>
          <div className="relative z-10">
            <SearchBar compact />
          </div>
        </div>
      </header>

      <main id="main-content" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        {children}
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 sm:px-6">
          <nav className="flex flex-wrap gap-x-4 gap-y-2" aria-label="푸터 메뉴">
            {FOOTER_LINKS.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className="text-sm text-text-tertiary no-underline hover:text-brand"
              >
                {label}
              </Link>
            ))}
            <a
              href={`${SITE_BASE}/sitemap.xml`}
              className="text-sm text-text-tertiary no-underline hover:text-brand"
            >
              Sitemap
            </a>
          </nav>
          <div className="flex flex-col gap-2 text-sm text-text-tertiary sm:flex-row sm:items-center sm:justify-between">
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
              href="https://github.com/sukoji/teams-news"
              className="text-brand no-underline hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              GitHub — sukoji/teams-news
            </a>
            <span className="text-xs">
              JSON: {SITE_BASE}/data/latest.json · {SITE_BASE}/data/feeds.json
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
