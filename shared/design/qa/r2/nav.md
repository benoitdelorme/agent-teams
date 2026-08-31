# qa: nav — round 2 (ref/nav@800.png vs qa/nav.png · ref/m-nav@800.png vs qa/m-nav.png)

## desktop (1440)
med CTA label weight — expected: regular/medium "VIEW RESOURCES" (ref, components/CTA.md font/label) / got: still bold (label ink ~35% denser than ref; glyphs visibly heavier)
fixed (r1): CTA right margin (now 28px@800 = ref), pill width (103 vs 102 @800 = ref), logo (identical bounds)

## mobile (390)
med CTA label weight — expected: regular/medium (ref) / got: still bold (label ink ~40% denser than ref)
fixed (r1): pill x 216→364 vs ref 218→364, h 42 vs 40 — within 2px jitter
