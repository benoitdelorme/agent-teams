# qa/design-intent — round 2 (2026-08-24)

## desktop (ref/design-intent@800.png vs qa/design-intent.png, 1440→800; ×1.8 for 1440 values)
r1 diffs fixed: title no longer too high, gaps no longer 2.4×. Remaining:
med  body line-height — expected: 2 lines at pitch 13px@800 (24px @1440, ref line tops y175/y188) / got: pitch ~11px@800 (~20px @1440, lines merge into one band y171-190) — body line-height ~4px too tight at 1440; font size itself matches (same x-extent 257-542)
med  title→body gap — expected: 31px@800 (title bottom y144 → body top y175) / got: 25px (y146 → y171) — ~11px too tight at 1440
low  body→tagline gap — expected: 29px@800 (y196 → y225) / got: 25px (y190 → y215) — ~7px too tight at 1440 (partly a consequence of the body line-height)
ok   block height 344 vs 345, group vertical centering (±4px), title size/position, tagline size/tracking, colors, text, horizontal centering

## mobile (ref/m-design-intent@800.png vs qa/m-design-intent.png, both 390)
r1 diffs fixed: block height now 450 (was 465), title→body no longer +23. Remaining:
med  body→tagline gap — expected: 36px (body bottom y279 → tagline top y315) / got: 45px (y269 → y314) — 9px too loose
med  title→body gap — expected: 33px (title bottom y191 → body top y224) / got: 26px (y189 → y215) — 7px too tight (content block shifted up ~3px overall as a result)
ok   block height 450, title 2-line pitch 51, body 3-line pitch 21, tagline 2-line pitch 22, all x-extents identical (wraps, sizes, side padding), colors, text
