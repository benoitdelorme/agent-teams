# qa/design-intent — round 3 (2026-08-24)

## desktop (ref/design-intent@800.png vs qa/design-intent.png, 800 scale; ×1.8 for 1440 values)
r2 fixed: body line-height now 2 lines at pitch 13@800 (24@1440), title size/position, tagline size, horizontal centering, block height 344. Remaining:
med  title→body gap — expected: 31px@800 (title bottom y144 → body top y175) / got: 26px (y144 → y170) — ~9px too tight at 1440
low  body→tagline gap — expected: 30px@800 (body bottom y196 → tagline top y226) / got: 26px (y191 → y217) — ~7px too tight at 1440
low  content group — expected: y118–232 (center y175) / got: y117–223 (center y170) — sits ~9px@1440 high, consequence of the two tight gaps
ok   title 117–144, body 2×(8px glyph, pitch 13), tagline 7px glyph, x-extents 216–583, colors, text

## mobile (ref/m-design-intent@800.png vs qa/m-design-intent.png, both 390)
r2 fixed: body position now identical (y225–279). Regressed/remaining:
med  title→body gap — expected: 34px (title bottom y191 → body top y225) / got: 47px (y178 → y225) — 13px too loose (r2 was 7px too tight; overshot), title pushed up to y95 (ref y108)
med  body→tagline gap — expected: 36px (body bottom y279 → tagline top y315) / got: 45px (y279 → y324) — 9px too loose (unchanged from r2), tagline y324–357 vs ref y315–348
ok   block height 450, title 2-line pitch 50/51, body 3-line pitch 21, tagline 2-line pitch 22, x-extents 34–354, group vertical center (y226 vs y228), colors, text
