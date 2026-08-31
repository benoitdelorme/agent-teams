# qa/design-intent — 2026-08-24

## desktop (ref/design-intent@800.png vs qa/design-intent.png, 1440→800)
med  title→body gap — expected: ~25px at 800 scale (spec col gap ~110 incl. line-height slack; title glyph bottom y148 → body top y172) / got: ~61px (title bottom y127 → body top y188) — title sits ~20px too high, body ~15px too low; gap roughly 2.4× the reference (~+65px at 1440)
med  body→tagline gap — expected: ~28px (body bottom y195 → tagline top y223) / got: ~22px (y212 → y234) — ~10px too tight at 1440
low  block height — expected: 345 / got: 344 (1px, ignore)
ok   bg color/ink, title size/weight/tracking, body size/color, tagline size/weight/color/uppercase, text content, horizontal centering, vertical centering of the group — all match

## mobile (ref/m-design-intent@800.png vs qa/m-design-intent.png, both 390 wide)
med  block height — expected: 450 / got: 465 (+15px)
med  title→body gap — expected: ~27px (title bottom y195 → body top y222) / got: ~50px (y195 → y245) — +23px at 390 scale
med  body→tagline gap — expected: ~31px (body bottom y282 → tagline top y313) / got: ~17px (y305 → y322) — 14px too tight
ok   bg, title 50px 2-line wrap, body 14px 3-line wrap, tagline 18px bold 2-line wrap, colors, text content, side padding — all match
