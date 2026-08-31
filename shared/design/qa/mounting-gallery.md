# qa/mounting-gallery — round 2 — 2026-08-24
A: ref/MediaCard@800.png (card 1) + ref/mounting-gallery@800.png (card 2) · B: qa/mounting-gallery.png (1440, whole block) · mobile: qa/m-mounting-gallery.png (390, vs spec only)
r1 recheck: label wrap (high) fixed · label weight (med) fixed · label width/tracking (med) fixed · mobile wrap (high) fixed · mobile font-size (med) fixed

## desktop — faithful
ok label wrap — "CEILING / SURFACE", "PENDANT / STEM", "PENDANT / CABLE" on two lines; "POST TOP" single line (fits the 388 box, as in Figma)
ok label weight/width — 2x crop of card-1 label vs ref: identical stroke weight (ExtraLight hairline), glyph width and line spacing; position left 122 / top 100 within 2 px on cards 1 and 2
ok image crops — cards 1 and 2 match refs; cards 3-4 consistent with spec assets; 4 × 800 stacked, 0 gap
ok text content — 4 labels correct and in order

## mobile (vs spec geometry) — faithful
ok label wrap — two lines on cards 1-3 within the 180×85 box ("CEILING" ≈ 150 px wide); "POST TOP" single line
ok label size/position — cap height consistent with 40px/40px; left 25 / top 50 within 2 px on all 4 cards
ok cards 390×500, 0 gap; cards 3-4 show the distinct mobile crops (lobby close-up, exterior) as spec'd
