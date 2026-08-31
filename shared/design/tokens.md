# Design tokens — Figma variables of the file (design fills `figma value`, frontend fills `code`)

file: fhdXQci2DTULtLlhVhg2I5   extracted: 2026-08-24 by design-extract (`get_variable_defs` on 20-118 desktop + 20-3 mobile, merged; identical sets — no responsive variable override)
Real Figma variables exist but are unnamed (hex-named). 3 color variables found, no font/space/radius variables in the file — those below are `derived` from get_design_context on 20-196 (text band) and 20-228 (nav).
Specs reference tokens BY NAME. Frontend maps each name once to its theme (Tailwind v4 `@theme` var, CSS var…) in `code`.

## color
| name | figma value | code | note |
|------|-------------|------|------|
| color/ink | #101820 | text-ink / bg-ink (--color-ink) | variable — near-black, used as dark bg (nav) and heading text |
| color/text-secondary | #616869 | text-text-secondary (--color-text-secondary) | variable — body copy gray |
| color/border-subtle | #CECCCC | text-border-subtle / border-border-subtle (--color-border-subtle) | variable — also used as body text on dark bands (defining-center, design-intent) |
| color/white | #FFFFFF | text-white | derived — nav logo/CTA text+border on dark bg |

## space
| name | figma value | code | note |
|------|-------------|------|------|
| space/nav-height | 80px | h-nav (--spacing-nav) | derived — nav bar (20:229) height |
| space/pill-pad-x | 30px | px-pill-x (--spacing-pill-x) | derived — CTA pill horizontal padding |
| space/pill-pad-y | 18px | py-pill-y (--spacing-pill-y) | derived — CTA pill vertical padding |
| space/title-body-gap | 40px | mt-title-body (--spacing-title-body) | derived — gap between display title and body paragraph (20:196) |

## type (font / size / line-height / weight)
| name | figma value | code | note |
|------|-------------|------|------|
| font/display | Work Sans ExtraLight 70px/70px, uppercase | font-sans font-extralight text-display uppercase | derived — hero/section title (20:200) |
| font/body | Work Sans Regular 16px/24px | text-body | derived — paragraph copy (20:199) |
| font/label | Work Sans Regular 14px/14px, uppercase | font-normal text-label uppercase | derived — nav CTA label (20:231); QA r3: Medium rendered ~35% denser than ref, Regular matches (frontend maps `code`) |

## radius · shadow · other
| name | figma value | code | note |
|------|-------------|------|------|
| radius/pill | 30px | rounded-pill (--radius-pill) | derived — nav CTA button (fully rounded pill at this height) |
