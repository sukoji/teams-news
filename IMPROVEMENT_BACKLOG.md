# PIAI Teams News — Improvement Backlog

> **Constraint:** Never modify Teams cron, `cron.yml`, digest schedule, or Teams posting pipeline in loop iterations.

Prioritized items for future UX/functionality rounds. Last updated: 2026-06-22.

## Article Detail Page

Research reference: [GeekNews](https://news.hada.io) topic pages (related posts, comments, metadata, share), Hacker News item pages (points, comments count, prev/next), Lobsters (tags, domain).

| Priority | Feature | Status | Notes |
|----------|---------|--------|-------|
| **P0** | Route `/item/:id` — wide reading layout | ✅ Done | React Router + GitHub Pages 404.html SPA pattern |
| **P0** | Title, source badge, date, section, engagement metrics | ✅ Done | Stars/Upvotes/Points on detail header |
| **P0** | Korean summary + `[원문 보기]` link | ✅ Done | Full summary (no line-clamp), external link |
| **P0** | Related news — "함께 보면 좋을 뉴스" | ✅ Done | Topic taxonomy + tag overlap + section + fuse.js tiebreaker |
| **P0** | Back navigation + breadcrumb | ✅ Done | 홈 → 피드 → 섹션 trail + 뒤로 button |
| **P0** | Share URL (copy link / Web Share API) | ✅ Done | Per-article detail page URL |
| **P0** | Mobile responsive wide card | ✅ Done | max-w-3xl article, stacked sidebar |
| **P0** | Cards link to detail page (not external only) | ✅ Done | NewsCard title → `/item/:id`; 원문 → external |
| **P1** | "More from this source" sidebar | ✅ Done | Top 5 same-source + link to `/source/:slug` |
| **P1** | Same-day digest context badge | ✅ Done | "YYYY-MM-DD Top 7 #N" when URL/id matches digest |
| **P1** | Tags/keywords chips (click → search) | ✅ Done | `matched_keywords` as filter links |
| **P1** | GeekNews comments link | ✅ Done | When source is GeekNews, link to topic `#comments` |
| **P1** | Per-article og:description + og:url | ✅ Done | `usePageMeta` with article type |
| **P1** | Previous/next in archive | ⏳ Pending | Chronological nav within section or global feed |
| **P1** | Reading time estimate | ⏳ Pending | ~200 wpm on summary length |
| **P1** | Bookmark / save locally | ⏳ Pending | localStorage saved items list |
| **P1** | Open in new tab vs in-app preference | ⏳ Pending | User setting for card click behavior |
| **P2** | Comments / discussion embed | ⏳ Pending | GeekNews/HN comment counts; no backend for our own |
| **P2** | Print-friendly view | ⏳ Pending | `@media print` stylesheet |
| **P2** | JSON-LD structured data (Article) | ⏳ Pending | SEO for `/item/:id` in sitemap |
| **P2** | og:image per article | ⏳ Pending | Branded fallback or source favicon |
| **P2** | Duplicate/cluster detection UI | ⏳ Pending | "같은 주제" — same URL or title fuzzy match (partial: topic badges on related cards) |
| **P2** | Section navigation at bottom | ⏳ Pending | Prev/next in same section chips |
| **P2** | Article pages in sitemap.xml | ⏳ Pending | Static generation or top-N items |
| **P2** | Full article body (GeekNews GN+ style) | ⏳ Pending | Would need ingest of full text; summary only now |
| **P2** | HN-style points/comments count | ⏳ Pending | Scrape or API for external sources |
| **P2** | Related by co-occurrence in digest | ⏳ Pending | Items appearing same day/section in Top 7 |

### Next loop priorities (Article Detail Page)

1. **P1** Previous/next archive navigation
2. **P1** Reading time estimate
3. **P1** localStorage bookmarks
4. **P2** JSON-LD + sitemap entries for `/item/:id`
5. **P2** Duplicate/cluster "같은 주제" banner (topic inference exists; cluster UI pending)

### Related news taxonomy (2026-06-22)

- ✅ **Done:** `web/src/lib/topics.ts` — keyword-pattern classifier (16 categories, entity tags)
- ✅ **Done:** `getRelatedItems()` scores primary topic → tag overlap → section → fuse.js
- ✅ **Done:** Related card topic badge + article "이 글의 주제" chips
- ⏳ **Future:** ML embedding similarity, user feedback on related quality, Python-side topic at ingest

---

## P0 — High impact / broken

| Item | Notes |
|------|-------|
| **Comments / discussion** | GeekNews has threaded comments & voting; we link out only (detail page has GeekNews link) |
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
| **Share button per card** | Copy link + Web Share API for individual items (detail page done; cards pending) |
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
| **Server-side / embedding search** | Live client fuse.js search done (2026-06-22); future: vector similarity, server index for large archives |

## What we beat GeekNews (keep investing)

- Section-balanced daily digest (Papers · News · Trending · Community)
- Korean summaries for international sources
- Engagement metrics (Stars, Upvotes) on cards
- Section-specific RSS + JSON API + extended metadata feed
- Dark/light mode, StyleSeed Linear design system
- Archive search with filters, sort, shareable URL state
- **Live search-as-you-type** — debounced input, instant fuse.js results, URL sync (`?q=`), header preview dropdown, empty states
- Microsoft Teams Adaptive Card delivery
- Multi-source aggregation beyond HN-style link board

## Completed this round (2026-06-22)

- **Live search-as-you-type** — 200ms debounce, memoized fuse.js, instant NewsCard grid, `?q=` URL sync, header preview dropdown, 검색어/결과 없음 empty states
- **Related news taxonomy** — topic classifier (`topics.ts`), improved scoring, Korean topic badges
- **Article detail page** at `/item/:id` — wide layout, breadcrumb, back nav
- **함께 보면 좋을 뉴스** — same-topic recommendations via taxonomy (not loose similarity only)
- **More from source** sidebar + digest Top 7 badge (URL-matched)
- **Share URL** — clipboard + Web Share API; per-article og meta
- **NewsCard** titles link to detail page; 원문 remains external
- Keyword chips → search; GeekNews comments link on detail page
- IMPROVEMENT_BACKLOG.md Article Detail Page section with P0/P1/P2

## Completed (2026-06-20)

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
