# PIAI Teams News — Web

Static React site for the daily AI/tech digest. Built with **Vite + React + TypeScript + Tailwind v4** and styled with [StyleSeed](https://github.com/bitjaru/styleseed).

## StyleSeed integration

### Skin choice: **Linear**

Linear’s dark-first palette and restrained shadows fit a dev/tech news digest audience. Brand accent `#5e6ad2` (light) / `#7170ff` (dark) is used sparingly for active nav, chips, and links per StyleSeed’s single-accent rule.

### Files copied from StyleSeed

| Source (StyleSeed repo) | Destination |
|-------------------------|-------------|
| `engine/css/fonts.css` | `src/styleseed/css/fonts.css` |
| `engine/css/base.css` | `src/styleseed/css/base.css` |
| `skins/linear/theme.css` | `src/styleseed/css/theme-linear.css` (adapted: `html[data-skin="linear"]` + `html.dark[data-skin="linear"]`) |
| `engine/DESIGN-LANGUAGE.md` | `src/styleseed/DESIGN-LANGUAGE.md` (reference) |
| `engine/components/ui/badge.tsx` | `src/styleseed/components/ui/badge.tsx` |
| `engine/components/ui/utils.ts` | `src/styleseed/components/ui/utils.ts` |
| `engine/components/patterns/section-card.tsx` | `src/styleseed/components/patterns/section-card.tsx` |

### Theme activation

- `index.html` sets `data-skin="linear"` on `<html>`.
- Dark/light toggle adds/removes `.dark` on `<html>`; tokens switch via CSS variables in `theme-linear.css`.
- App styles in `src/index.css` import StyleSeed layers and add project utilities (`.ss-card`, `.ss-chip`) following DESIGN-LANGUAGE rules: cards on page background, one accent, restrained shadows, pill section toggles.

### Design rules applied

- **Cards on background** — page uses `--surface-page`, cards use `--card` with subtle border/shadow.
- **One accent** — `--brand` only for active states, links, engagement metrics.
- **Visual rhythm** — hero (type D) → pill nav → 2-column card grid on Home; section headers + cards on other pages.
- **Dark mode** — card surface brighter than page background (`#0f1011` vs `#08090a`).

## Development

```bash
cd web
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output goes to `web/dist/` and is copied to `web/public/` by the Python export pipeline (`outputs/export.py`).

## Pages

| Route | Description |
|-------|-------------|
| `/` | Today’s digest — hero, section chips, 2-col grid |
| `/archive` | Date index |
| `/date/:date` | Historical digest |
| `/subscribe` | RSS & JSON feed URLs |
| `/about` | Curation policy |

## License note

StyleSeed components and CSS are [MIT licensed](https://github.com/bitjaru/styleseed/blob/main/LICENSE). Copied files retain StyleSeed attribution in their source headers where present.
