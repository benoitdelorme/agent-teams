# qa: nav (ref/nav@800.png vs qa/nav.png · ref/m-nav@800.png vs qa/m-nav.png)

## desktop (1440)
med CTA label weight — expected: regular/medium weight "VIEW RESOURCES" (ref, components/CTA.md) / got: bold weight
med CTA right margin — expected: ~50px from right edge (ref; spec left 1205 + pill width) / got: ~32px (pill sits ~18px further right)
med CTA pill width — expected: ~187px (ref) / got: ~196px (wider, consistent with bold label)
low logo — expected: wordmark + thin rule above (asset) / got: same, rule renders slightly heavier (likely antialias at 800 scale)

## mobile (390)
med CTA label weight — expected: regular/medium weight (ref) / got: bold
low CTA pill — expected: x 218→364 (ref) / got: x 216→364 (~1px at 390 scale, within jitter)
