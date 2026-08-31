# qa/gallery-family — 2026-08-24
A: ref/gallery-family@800.png, ref/m-gallery-family@800.png · B: qa/gallery-family.png, qa/m-gallery-family.png

## desktop (1440 → 800)
faithful — no diffs. All three lamps (two pendants left/top-centre, floor lamp right) at identical position, crop and scale; stem/cable positions, highlight and background gradient match. ImageMagick RMSE 0.8% (compression noise). B is 800×533 vs A 800×534: rounding, ignored.

## mobile (390)
faithful — no diffs. Same crop: left pendant cut at left edge, top pendant centred, floor lamp right with stem running to bottom edge. RMSE 0.4%.

## note
Spec describes a 3-photo blob-mask collage; the Figma reference renders as one seamless photo (mask edges invisible), and the app reproduces exactly that. Nothing to fix.
