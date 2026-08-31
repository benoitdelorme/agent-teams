# home/closeup
figma: fhdXQci2DTULtLlhVhg2I5 node 20:176     ref: ref/closeup@800.png     extracted: 2026-08-24 hash 20176

size: 1440×960 (desktop only) · full-bleed, no bg fill of its own (photos cover the frame; base rect Rectangle 2 is 1440×960 but fully covered)

## Layout (tree — all 3 photos are absolutely positioned, no auto-layout; overflowing edges are clipped to the 1440×960 block bounds)
frame (clip: 0,0 1440×960)                         ← block root
  image  assets/closeup/he-shooting-surface-x2-closeup-03.jpeg   x 0  y 0  w 1499  h 1000   object-fit cover   ← overflows right edge by 59px and bottom edge by 40px (clipped)
  image  assets/closeup/he-shooting-stem-bg-dark.jpeg            x 0  y -290  w 1440  h 1440   object-fit cover   ← starts 290px ABOVE the block's top edge (clipped) and overflows bottom by 190px (clipped); sits behind the other two in paint order (background layer)
  image  assets/closeup/he-shooting-cable-hand.jpeg              x 0  y 0  w 1428.8  h 950.1   object-fit cover   ← nearly full-bleed, 11px short of right edge and 10px short of bottom edge

Paint order (back to front): stem-bg-dark → surface-x2-closeup-03 → cable-hand. All three are plain photographic fills, no borders/radius/shadow — the frame itself clips everything to 1440×960.

## Data
No text content in this block — pure image stack.

## Tokens used
None — no color/type/space tokens apply; this block is images only.
raw (no token found): all geometry above is raw px (no matching space tokens; these are one-off photo placements, not spacing).

## States / variants seen
None — static image stack, no interactive elements.

## Breakpoints
Mobile has no separate frame for this block: on mobile the closeup imagery is merged into home/focal-statement (node m 20:59, which holds the closeup image plus 2 hidden alt images). See blocks/home/focal-statement.md for the mobile treatment — do not implement this spec on mobile.

## Adjacent-block overlap
home/focal-statement's large heading text (node 20:185, "When light is the focal point, space becomes composed.") visually overlaps this block's top edge: the text box sits at x 122 y -284 (relative to this block's top-left, i.e. 284px above the block) w 908 h 417, so its bottom edge intrudes 133px down into this block's top. Implement the heading in focal-statement.md; when stacking the two blocks in a page, allow focal-statement's text to overlap 133px into the top of this block (e.g. negative margin or overlapping absolute stack) rather than adding spacing here.

## Assets
assets/closeup/he-shooting-surface-x2-closeup-03.jpeg (source 4096×2732)
assets/closeup/he-shooting-stem-bg-dark.jpeg (source 4096×4096)
assets/closeup/he-shooting-cable-hand.jpeg (source 4096×3000)
