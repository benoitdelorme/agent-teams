# qa: home/intro — round 2 — 2026-08-24
ref/intro@800.png vs qa/intro.png · ref/m-intro@800.png vs qa/m-intro.png (mobile 390 wide, 1:1). Round-1 diffs re-measured: none fixed.

## Desktop (1440, measured at 800 → ×1.8) — 3 diffs (med 1, low 2)
med  gap title→body — expected: 31px @800 between title bottom (row 144) and body top (row 175), ≈56px real / got: 25px @800 (title 116–143, body 168–176), ≈45px real — body ~6px @800 (≈11px real) too high. r1: 24px → unchanged.
low  body line-height — expected: line pitch 13px @800 (16/24 real, rows 175→188) / got: pitch 11px @800 (rows 168→179, ≈20px real) — line-height still ~4px real too tight. r1 → unchanged.
low  block edge hairline — expected: pure white top and bottom / got: r1's row-0 dark hairline is gone, but the last row (305) is now dark (mean 0.76 vs 1.0) — a 1px border-bottom / bleed from the next block. Moved, not removed.
Match: structure, text, uppercase, centering (title x 152–645, body x 185–614 identical), title size/weight (title 2px higher, within jitter), colors.

## Mobile (390) — 1 diff (low 1)
low  gap title→body — expected: 33px (title bottom row 192 → body top 225) / got: 29px (body top 221); all five body lines 4px higher, pitch 21px identical in both. r1 → unchanged.
Match: title rows identical (108–142, 158–192), wrapping (2 title / 5 body lines), x-extents (31–357), size, colors, block height (421 vs 420).
