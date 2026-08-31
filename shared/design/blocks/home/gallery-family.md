# home/gallery-family
figma: fhdXQci2DTULtLlhVhg2I5 node 20:191 [mobile 20:74]   ref: ref/gallery-family@800.png / ref/m-gallery-family@800.png   extracted: 2026-08-24 hash 20:191

size: 1440×960 (desktop) · full-bleed image collage, clipped to block bounds (overflow hidden)

## Layout (tree)
box (clip bounds 1440×960, no bg fill — photos fill the frame)   ← the block root
  image  assets/gallery-family/he-shooting-family-bg-light.png   x -80  y -80  w 1439.7  h 1323   clip-mask collage-mask.svg
  image  assets/gallery-family/he-shooting-stem-x2-bg-dark.png    x 0    y 0    w 1484    h 990    clip-mask collage-mask.svg
  image  assets/gallery-family/he-shooting-surface-x2-closeup-04.png  x 1440  y -34  w 1505  h 1004  clip-mask collage-mask.svg  rotate 180°

All three photos share the same organic blob clip-mask (collage-mask.svg), just scaled/positioned/rotated per photo. Coordinates are relative to the block's top-left (0,0 = 1440×960 frame origin). Stacking order top→bottom as listed (family-bg-light behind, closeup-04 in front, rotated 180°).

## Data
none (image-only block, no text)

## Tokens used
none matched in tokens.md (all raw geometry, no color/type/radius involved — pure photo collage)
raw: photo offsets/sizes above (px, from Figma node metadata)

## States / variants seen
none

## Breakpoints
mobile 390 (node 20:74, frame 390×520, same clip approach, mask svg reused):
  image  he-shooting-family-bg-light.png   x -129  y 0  w 566  h 520
  image  he-shooting-stem-x2-bg-dark.png    x -192  y 0  w 780  h 520
  image  he-shooting-surface-x2-closeup-04.png  x 651  y 0  w 780  h 520  rotate 180°  (offscreen right, only left ~129px sliver visible)
  Same 3 source photos as desktop, only crop/position via mask differs — do not re-export per breakpoint, reuse the same 3 image files with CSS position/size per breakpoint.

## Assets
assets/gallery-family/he-shooting-family-bg-light.png (source photo)
assets/gallery-family/he-shooting-stem-x2-bg-dark.png (source photo)
assets/gallery-family/he-shooting-surface-x2-closeup-04.png (source photo)
assets/gallery-family/collage-mask.svg (shared clip-mask shape, 390×520 native, scale to fit each photo's box)
