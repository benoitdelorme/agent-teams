# qa/focal-statement — 2026-08-24

## desktop (ref/focal-statement@800.png vs qa/focal-statement.png, 800 = 1440 × 0.556)
med  h1 vertical position — expected: text box top 1156 (284 above montage bottom) → first cap top ≈ 1174 / got: first cap top at 1188 (800px y=660) → text sits ≈ 14px too low. Derived from Work Sans metrics; same method gives a 3px match on mobile, so the offset is credible but ±5px.
ok   montage crop — identical to ref (mean gray diff 2.3/255, resampling only).
ok   h1 x inset — expected 122 / got 124. Font size 100 (cap 67px) and line-height 100 (pitch 100) match. Wrap "WHEN LIGHT IS / THE FOCAL POINT, / SPACE BECOMES / [COMPOSED.]" fits the 908×417 box (4 lines); 4th line lies below the montage edge as spec'd.
n/a  text content/style vs Figma — statement (20:185) absent from ref; judged against spec px only (content, weight split ExtraLight/Bold, uppercase, white match the spec).

## mobile (ref/m-focal-statement@800.png vs qa/m-focal-statement.png, both 390 = 1:1)
ok   montage crop — pixel-identical to ref (mean diff 0.0).
ok   h1 — expected x=10, box top 520, 55/55 / got x=11, cap top 527 (≈ box top 517), line pitch 55, cap 36px. 6 lines "WHEN LIGHT / IS THE FOCAL / POINT, / SPACE / BECOMES / COMPOSED.", last baseline 838 (box bottom 850 ⇒ +98 overlap into closeup as spec'd).
ok   closeup — starts at y≈746-750 (≤ 4px), full-bleed 390×520, image content plausible; no ref for the closeup crop (20:59 not screenshotted), not compared pixelwise.
n/a  text vs Figma — 20:68 absent from ref; wrap inferred from the 370×328 box (6 × 55), not from Figma rendering.

VERDICT desktop: 1 diff (med: h1 ≈ 14px low) · mobile: faithful
