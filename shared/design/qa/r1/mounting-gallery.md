# qa/mounting-gallery — 2026-08-24
A: ref/MediaCard@800.png (card 1, 20:166) + ref/mounting-gallery@800.png (card 2, 20:161) · B: qa/mounting-gallery.png (1440) · mobile: qa/m-mounting-gallery.png (390, no ref — judged vs spec only)

## desktop (cards 1 & 2 vs refs) — 3 diffs (high 1, med 2, low 0)
high label wrap (cards 1–4) — expected: label box 388×222 → two lines "CEILING / SURFACE", "PENDANT / STEM" (ref) / got: single line "CEILING SURFACE", "PENDANT STEM" — no width constraint on the label
med label weight — expected: font/display Work Sans ExtraLight, hairline strokes (ref) / got: visibly heavier strokes (reads Light/Regular); verify weight 200 is loaded and applied
med label width/tracking — expected: "CEILING" ≈ 250px wide at 1440 (ref) / got: ≈ 280px — glyphs slightly wider (consistent with the heavier weight, or letter-spacing added)
ok label position — left 122 / top ~100 at 1440: matches within ~5px on both cards
ok image crop — card 1 (fixture centred under wood ceiling, kitchen left, window right) and card 2 (pendant centred between corner windows) match refs; card heights 800 each, 0 gap
ok text content — 4 labels correct and in order; cards 3–4 not ref'd (images plausible vs spec asset names)

## mobile (vs spec geometry only, no Figma ref) — 2 diffs (high 1, med 1)
high label wrap — expected: label box 180×85 at 40px → two lines ("CEILING / SURFACE") / got: single line spanning ~325px of the 390 card
med label font-size — expected: 40px/40px (raw) / got: ≈ 36–38px estimated from cap height; borderline, recheck once the wrap is fixed
ok label position — left 25, top ~50 matches; cards 390×500, 0 gap; image crops cover-fit as spec'd
