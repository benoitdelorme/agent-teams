# qa/defining-center — round 2 (2026-08-24, after frontend fix; spec gaps 41/36 desktop, 22/27 mobile)

## desktop (1440, measured on 800px renders — ink-to-ink row bands, ×1.8 to 1440)
med title→body gap — expected: ~56px ink gap (ref rows 144→175 = 31 @800) / got: ~45px (146→171 = 25 @800), ~11px too tight
med body→tagline gap — expected: ~52px ink gap (ref 196→225 = 29 @800) / got: ~43px (191→215 = 24 @800), ~9px too tight
Both gaps short by a similar ~10px → likely line-box slack (Figma text box vs browser line-height), not the 41/36 values themselves; content block is ~20px shorter overall, still vertically centered.
Faithful: bg #616869, title size/tracking/x-extent (199–603), body 2-line wrap + line pitch + x-extent, tagline size/weight/x-extent (227–571), block height 344 vs 345, text content.
r1 diffs (25/85 gaps) are fixed.

## mobile (390, 1:1)
low block height — expected: 470px (ref) / got: 477px (+7, content otherwise at same y ±3)
Faithful: title→body gap (ref 82 / got 85), body→tagline gap (ref 35 / got 36), body line pitch 21, 4-line body wrap, 2-line title and tagline wraps, all x-extents identical, text content.
r1 diffs are fixed.
