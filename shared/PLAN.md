# Feature: Hollowcore — responsive landing page (2 Figma frames)

## Goal (2 lines)
Implement Figma frames `20-118` (home, desktop 1440) and `20-3` (m-home, mobile 390) from file `fhdXQci2DTULtLlhVhg2I5` — two breakpoints of ONE page → one responsive page at public route `/hollowcore` in sample-frontend (React 19 + Tailwind 4 + react-router), pixel-faithful at 1440 and 390.
Design extracts block specs (desktop+mobile per block); frontend implements; design does visual QA. No backend work expected (static content).

## Tasks
| id | team | task (1 line) | criteria (1 line) | status | notes |
| D1 | design | Extract specs for the 11 blocks + 2 components already listed in design/MANIFEST.md: one spec per block covering desktop 1440 AND mobile 390; assets exported to design/assets; tokens.md filled | every block/component `extracted` in MANIFEST with spec path; assets present; SPEC sent to frontend | done | done 2026-08-24: 11 blocks + 2 components, 9 asset dirs, 24 refs; no autolayout conversion (out of criteria). Figma: ...?node-id=20-118 (home) / ...?node-id=20-3 (m-home) |
| F1 | frontend | Page src/pages/Hollowcore.tsx + public route `/hollowcore` (outside RequireAuth): blocks nav, hero, intro, gallery-family, defining-center, focal-statement, closeup + components CTA, MediaCard | `pnpm build` + `pnpm lint` green; blocks match spec at 1440 and 390 | done | depends D1 (SPEC) |
| F2 | frontend | Same page: blocks design-intent, mounting-gallery, resources, footer | same as F1; full page scrolls end-to-end at both breakpoints | done | depends D1; can be done in the same pass as F1 |
| D2 | design | Visual QA of /hollowcore at 1440 and 390 vs Figma refs; SPEC-DIFF to frontend if gaps, else DONE | qa/<block>.md per diff; every block `qa-ok` in MANIFEST | done | depends F1,F2 |
| F3 | frontend | Fix SPEC-DIFF gaps from D2 | build/lint green; design re-QA → qa-ok | waiting-human | 3 rounds done; residual: text-band title→body gap ≈9px (Figma text box vs browser) — human decides |
| D3 | design | Auto-layout conversion of EVERY block of both frames (home 20-118, m-home 20-3) on Figma page `_autolayout` via tools/figma/autolayout.js; originals untouched | one copy per block on `_autolayout`, leaf bbox delta ≤ 1px, `skipped` containers listed with reason per block in MANIFEST notes; design-vision verdict `faithful` on blocks with skips; DONE lists converted/skipped counts | done | human replaces originals in Figma after review; runs in parallel with F1/F2 (no dependency) |

## Contracts → CONTRACTS.md (none expected)
