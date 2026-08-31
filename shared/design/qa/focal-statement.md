# qa/focal-statement — round 2 — 2026-08-24

## desktop (ref/focal-statement@800.png vs qa/focal-statement.png, 800 = 1440 × 0.556)
faithful
fixed  h1 vertical position — r1: first cap top 1188 (≈14px low) / r2: first cap top 1174 (expected ≈1174 for box top 1156 = 284 above montage bottom). Line pitch 100 (caps at 1174 / 1274 / 1374), bold line "SPACE BECOMES" is line 3, "COMPOSED." falls below the 1440 edge as spec'd (+133 overlap, box bottom 1573).
ok     montage crop — identical to ref (resampling noise only).
ok     h1 x inset — expected 122 / got 124 (≤ 2px). Size 100 (cap 67), ExtraLight/Bold split, uppercase, white: match spec.
n/a    text vs Figma — statement absent from ref; judged against spec px.

## mobile (ref/m-focal-statement@800.png vs qa/m-focal-statement.png, 390 = 1:1)
faithful (unchanged from r1)
ok     montage crop — pixel-identical to ref.
ok     h1 — x=12 (expected 10), cap top ≈ 527, pitch 55 (bold lines at 692 / 747 / 802, cap 37), last baseline 838 ⇒ box bottom 850 = +98 overlap into closeup as spec'd. 6 lines as in r1.
ok     closeup — starts at montage bottom (≤ 4px), 390×520 full-bleed; no ref crop for 20:59, not compared pixelwise.

VERDICT desktop: faithful · mobile: faithful
