# Component: MediaCard
figma: fhdXQci2DTULtLlhVhg2I5 node 20:166 [mobile 20:49]   ref: ref/MediaCard@800.png   extracted: 2026-08-24 hash 20166166
size: 1440×800 (desktop) · full-bleed, no bg fill (image fills container)

## Layout (tree — indent = nesting; col/row = auto-layout direction)
box (absolute/full-bleed, no padding)                  ← card root, size fixed per breakpoint
  image  full-bleed cover  assets/media-card/hollowcore-2-0-office-04.png
    (source 1928×1072, cropped/scaled to fill card; no border/radius/shadow — bleeds to card edges)
  text  label  "Ceiling surface"  font/display  color/white  uppercase
    pos: left 122 top 100 (relative to card top, i.e. 6210-6110)  w 388  h 222

## Data (text content, in order; one line per repeated item)
label: "Ceiling surface" (raw text; siblings 08B/08C/08D reuse this component with different image + label, e.g. "Wall surface", "Floor surface" — not extracted, described only)

## Tokens used
color: color/white (label text)     type: font/display (Work Sans ExtraLight 70px/70px uppercase)
raw (no token found): label position (left 122, top 100), label box 388×222

## Props/variants
- image: path to full-bleed photo/video-still asset (source aspect ~1.8:1, cover-fit)
- label: uppercase string, top-left, font/display (desktop) / smaller size on mobile

## States / variants seen
No hover/interaction observed in this static frame. 4 sibling instances in the mounting-gallery (08A–08D) differ only by image + label.

## Breakpoints (only if several node ids)
mobile 390×500: label font/display scaled down to 40px/40px (not in tokens.md as separate token — flag `raw`), label pos left 25 top 50, label box 180×85. Image mask offset left -245 (bleeds beyond card bounds, cover-fit behavior).

## Assets
assets/media-card/hollowcore-2-0-office-04.png (1928×1072 source, used as full-bleed cover image)
