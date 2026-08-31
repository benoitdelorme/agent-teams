# Design manifest — state of every Figma block (owned by the design team)

Statuses: todo → autolayout → extracted → implemented → qa-ok | qa-diff · stale = Figma changed (hash), re-extract.
`nodeIds`: desktop first, then other breakpoints (`12:34 / m 12:90`). `hash` from tools/figma/meta-hash.py.
One table per page. Components are listed once at the bottom.
m-home rows share the desktop spec (blocks/home/<name>.md, section ## Breakpoints); mobile closeup lives in focal-statement.md.
D2 2026-08-24: QA round 2 done — residual qa-diff: nav (CTA weight), intro/defining-center/design-intent (body line-height 20→24, mobile gaps); round 1 archived in qa/r1/. QA round 1 done, see qa/<block>.md; qa-diff = frontend fix needed (specs defining-center/design-intent/resources corrected during QA).
D3 2026-08-24: auto-layout copies on Figma page `_autolayout` — autolayout column = `copy:yes|partial|none` (see qa/autolayout-summary.md for copy ids, skipped containers and the human-judgement list). Originals untouched; specs keep px geometry.

## Page: m-home   file fhdXQci2DTULtLlhVhg2I5   frame 20:3   split 2026-08-24
| name | nodeIds | size | role | autolayout | components | hash | status | spec |
|------|---------|------|------|------------|------------|------|--------|------|
| nav | m 20:110 | 390x70 | top bar: logo + "View resources" CTA | copy:none | CTA | 134a24e8 | qa-diff | blocks/home/nav.md |
| hero | m 20:84 | 390x450 | full-bleed photo (masked, 3 layered images) + HE_Sign logo overlay | copy:partial |  | 17484ccf | qa-ok | blocks/home/hero.md |
| intro | m 20:79 | 390x420 | "The center of attention" title + paragraph on flat bg | copy:yes |  | cb188633 | qa-diff | blocks/home/intro.md |
| gallery-family | m 20:74 | 390x520 | full-bleed image collage (3 photos, one offscreen right) | copy:none |  | ee1ceba8 | qa-ok | blocks/home/gallery-family.md |
| defining-center | m 20:69 | 390x470 | "Defining the Center" title + paragraph + tagline | copy:none |  | 24384c04 | qa-diff | blocks/home/defining-center.md |
| focal-statement | m 20:64 + 20:68 + 20:59 | 390x1270 | tall montage image, big quote text straddling into closeup image below (2 hidden alt images in 20:59) | copy:partial |  | 6c29b306+3f83c349+bb3cc762 | qa-ok | blocks/home/focal-statement.md |
| design-intent | m 20:54 | 390x450 | "Design Intent" title + paragraph + tagline | copy:none |  | e754b57a | qa-diff | blocks/home/design-intent.md |
| mounting-gallery | m 20:49 + 20:44 + 20:39 + 20:34 | 390x2000 | 4 stacked full-bleed media cards (Ceiling surface, Pendant stem, Pendant Cable, Post top) with label | copy:yes | MediaCard | bd821b13+7245e100+14efad1f+d453202e | qa-ok | blocks/home/mounting-gallery.md |
| resources | m 20:33 + 20:6 | 390x525 | "Explore resources" title + 5-row table (label + CTA, hairline dividers) | copy:partial | CTA | aca1c2f8+c26134e6 | qa-ok | blocks/home/resources.md |
| footer | m 20:5 | 390x915 | footer — flat reference image only (REF_m-Footer), no layers to extract | n/a |  | 71fa37c2 | qa-ok | blocks/home/footer.md |

## Page: home   file fhdXQci2DTULtLlhVhg2I5   frame 20:118   split 2026-08-24
| name | nodeIds | size | role | autolayout | components | hash | status | spec |
|------|---------|------|------|------------|------------|------|--------|------|
| nav | 20:228 | 1440x80 | top bar: logo, CTA 'View resources'; sticky candidate | copy:none | CTA | 078d3dd5 | qa-diff | blocks/home/nav.md |
| hero | 20:201 | 1440x880 | full-bleed photo (3 stacked/masked images), HE_Sign logotype (vector), scroll hint | copy:partial | — | 80b5dc97 | qa-ok | blocks/home/hero.md |
| intro | 20:196 | 1440x550 | white band (dark text): title 'The center of attention' + paragraph, centered 780px | copy:none | — | 4bc64bad | qa-diff | blocks/home/intro.md |
| gallery-family | 20:191 | 1440x960 | full-bleed image collage, 3 photos overflowing frame (clipped) | copy:none | — | 36a01a09 | qa-ok | blocks/home/gallery-family.md |
| defining-center | 20:186 | 1440x620 | dark band (#616869, white text): title + paragraph + tagline | copy:none | — | 1d979d74 | qa-diff | blocks/home/defining-center.md |
| focal-statement | 20:181 + 20:185 | 1440x1440 (+text 908x417) | full-bleed image; big statement text 20:185 overlaps bottom edge into next block | copy:partial | — | de89ef2d/7742c9a5 | qa-ok | blocks/home/focal-statement.md |
| closeup | 20:176 | 1440x960 | full-bleed image stack (3 photos, one overflowing 1440px) | copy:none | — | ac049730 | qa-ok | blocks/home/closeup.md |
| design-intent | 20:171 | 1440x620 | dark band (color/ink): title + paragraph + tagline (same layout as defining-center) | copy:none | — | 535cf587 | qa-diff | blocks/home/design-intent.md |
| mounting-gallery | 20:166 + 20:161 + 20:156 + 20:151 | 4 x 1440x800 | 4 identical sections: full-bleed video/photo + label top-left (Ceiling surface / Pendant stem / Pendant cable / Post top) | copy:yes | MediaCard | 81d182a0/a64f8468/ec3e41e2/680141d1 | qa-ok | blocks/home/mounting-gallery.md |
| resources | 20:119 (table 20:121, title 20:150) | 1440x810 | title 'Explore resources' + 5-row table (label + CTA), vertical rules at 280/1160 | copy:none | CTA | 502d1787 | qa-ok | blocks/home/resources.md |
| footer | 20:120 | 1440x470 | REF_Footer: flat reference image only, no layers to extract | n/a | — | 08e83613 | qa-ok | blocks/home/footer.md |

## Components (extract once, reference from blocks)
| name | nodeId | used in | hash | status | spec |
|------|--------|---------|------|--------|------|
| CTA | 20:230 / m 20:112 | home/nav, home/resources, m-home/nav, m-home/resources (7 occurrences: pill button, label + 40px height; not a Figma component) | 768ea5a4 / c41af41a | extracted | components/CTA.md |
| MediaCard | 20:166 / m 20:49 | home/mounting-gallery, m-home/mounting-gallery (4 identical frames 08A-08D: bg rect + oversized image + label; not a Figma component) | 81d182a0 / bd821b13 | extracted | components/MediaCard.md |
