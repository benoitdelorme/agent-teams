# qa/hero — ref/hero@800.png vs qa/hero.png · ref/m-hero@800.png vs qa/m-hero.png · spec blocks/home/hero.md

## desktop (1440 → 800)
med  scroll hint (right, top 796) — expected: 25×114 glyph as in ref, short leader line, "scroll" text legible, arrow below / got: glyph narrower (~12 px vs ~15 px at 800) with text vertically compressed and leader line longer — looks like the scroll-hint.jpg is scaled non-uniformly (aspect not preserved) or rendered at a smaller width; blend "lighten" is applied correctly (no black box)
low  photo crop/zoom — checked explicitly: lamp head spans x 218–512, top y 113, building edges and window grid at identical positions in A and B; crop is NOT zoomed vs ref (no diff)
low  logo lockup — "HOLLOWCORE" / "ELEMENT" position, size, weight, opacity match ref (no diff)

## mobile (390 → 800)
faithful — photo crop, logo lockup (240×73 at left 82 / top 397), no scroll hint: all match ref; no diffs
