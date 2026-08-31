# qa/hero — round 2 · ref/hero@800.png vs qa/hero.png · ref/m-hero@800.png vs qa/m-hero.png · spec blocks/home/hero.md

## desktop (1440 → 800)
r1 med scroll hint (glyph narrower, text compressed, leader line longer) — FIXED: glyph now 25×114 equivalent, right edge / top 796 match, leader line and arrow lengths match ref, blend "lighten" correct.
low  scroll hint "scroll" text — expected: letter strokes ~8 px wide column at 800, smooth antialiased as in ref / got: column ~6 px wide, strokes thinner and slightly pixelated (looks like the JPG is downscaled without smoothing or the text lane is very slightly squeezed); position, line and arrow are correct.
photo crop, logo lockup: unchanged from r1, match ref (no diff).

## mobile (390 → 800)
faithful — photo crop, logo lockup, absence of scroll hint all match ref; no diffs.
