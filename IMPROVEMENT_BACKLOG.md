# PIAI Teams News — Improvement Backlog

Prioritized items for future UX/functionality rounds. Last updated: 2026-06-20.

## P0 — High impact / broken

| Item | Notes |
|------|-------|
| **Comments / discussion** | GeekNews has threaded comments & voting; we link out only |
| **User accounts & bookmarks** | No auth layer; would need backend or local-only bookmarks |
| **GeekNews source in daily digest** | GeekNews in RSS list but often absent from Top 7 — tune scoring |
| **Infinite scroll option** | Pagination works; optional infinite scroll for mobile feed |
| **Search index compression** | ~65KB now; gzip at CDN or split index when archive >500 items |
| **Hourly ingest CI** | Verify `ingest.yml` runs archive append without breaking Pages deploy |

## P1 — UX polish

| Item | Notes |
|------|-------|
| **Mobile hamburger nav** | Horizontal scroll nav works; dedicated drawer for small screens |
| **Keyboard shortcuts panel** | `/` search exists; add `?` help overlay, `j`/`k` item navigation |
| **Share button per card** | Copy link + Web Share API for individual items |
| **Date archive deep pages SEO** | `/date/:date` not in sitemap; add dynamic sitemap generation |
| **Source / section landing pages** | Routes exist (`/source/:slug`, `/section/:id`); add nav links & meta |
| **Relative time SSR** | Client-only relative times; acceptable for static SPA |
| **Filter chips in URL bar UI** | Active filters as removable chips above results |
| **Pull-to-refresh on mobile** | PWA-style refresh for digest |
| **Loading retry button** | Error states have reload; add explicit retry without full reload |

## P2 — Nice to have

| Item | Notes |
|------|-------|
| **PWA / offline cache** | Service worker for digest + meta; full archive too large |
| **og:image per day** | Policy says no thumbnails; optional branded OG image for sharing |
| **Dark mode system sync default** | Theme toggle exists; respect `prefers-color-scheme` on first visit |
| **Analytics (privacy-friendly)** | Plausible/GA4 for popular queries & sections |
| **Email digest subscribe** | GeekNews has newsletter; we have RSS + Teams only |
| **Trending keywords cloud** | From `matched_keywords` in archive |
| **Duplicate detection UI** | Same story from multiple sources — cluster view |
| **i18n EN/KO toggle** | Korean-first; optional English UI strings |
| **Archive full-text search** | Currently title/summary/keywords only |

## What we beat GeekNews (keep investing)

- Section-balanced daily digest (Papers · News · Trending · Community)
- Korean summaries for international sources
- Engagement metrics (Stars, Upvotes) on cards
- Section-specific RSS + JSON API + extended metadata feed
- Dark/light mode, StyleSeed Linear design system
- Archive search with filters, sort, shareable URL state
- Microsoft Teams Adaptive Card delivery
- Multi-source aggregation beyond HN-style link board

## Completed this round (2026-06-20)

- Fixed `/feed` route shadowed by `feed/index.json` → moved to `data/feeds.json`
- Search match highlighting in cards
- Recent searches (localStorage) + `/` keyboard shortcut
- Shareable pagination (`?page=N`) in feed/search URLs
- Skeleton loading states (home + feed)
- Home stats bar (archive total, sources, days) + CTA to full feed
- “+N 신규” badge on feed since last visit
- Error boundary + improved offline/error messaging
- SEO: og meta tags, per-page titles, sitemap.xml, robots.txt
- Accessibility: skip link, aria labels, focus rings, touch targets
- Footer nav links; mobile filter drawer (Escape, scroll lock, aria-modal)
- Feed catalog JSON path update in Subscribe page
