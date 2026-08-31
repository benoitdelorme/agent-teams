# qa: home/intro — round 3 — 2026-08-24
ref/intro@800.png vs qa/intro.png · ref/m-intro@800.png vs qa/m-intro.png. Re-measured r2 residuals.

## Desktop (1440, measured at 800 → ×1.8) — 3 diffs (med 1, low 2)
med  gap title→body — expected: 31px @800 (title bottom 144 → body top 175, ≈56 real) / got: 26px @800 (141 → 167, ≈47 real) — still ≈9px real short. r2: 25px → +1, effectively unchanged.
low  block bottom hairline — expected: pure white last row / got: row 305 mean 202/255 — 1px dark line at bottom edge still there (border-bottom or next block bleeding). r2 → unchanged.
low  vertical position — expected: title rows 118–144 / got: 114–141 — whole content 4px @800 (≈7 real) higher than ref; block height identical (306), so top/bottom padding or centering is off by that amount.
Fixed since r2: body line-height — pitch now 13px @800 (175→188 vs 167→180), matches 16/24 real. Match: structure, text, uppercase, x-extents (152–644), title size, colors.

## Mobile (390, 1:1) — 1 diff (low 1)
low  gap title→body — expected: 33px (title bottom 192 → body top 225) / got: 29px (192 → 221) — body 4px too high, all 5 lines shifted equally; pitch 21px identical. r2 → unchanged (frontend gap 16 leaves it 4px short; ref implies ≈20).
Match: title rows identical (108–142, 158–192), wrapping, x-extents (31–357), size, colors, height (421 vs 420), no hairline.
