# home/mounting-gallery
figma: fhdXQci2DTULtLlhVhg2I5 node 20:166+20:161+20:156+20:151 [mobile 20:49+20:44+20:39+20:34]   ref: ref/mounting-gallery@800.png   extracted: 2026-08-24 hash 20161156
size: 1440×3200 desktop (4 × 1440×800 stacked) · 390×2000 mobile (4 × 390×500 stacked)

## Layout (tree — indent = nesting; col/row = auto-layout direction)
col gap 0                                              ← block root, 4 stacked full-bleed cards, no gap either breakpoint
  → components/MediaCard.md (image=assets/media-card/hollowcore-2-0-office-04.png, label="Ceiling surface")
  → components/MediaCard.md (image=assets/mounting-gallery/hollowcore-2-0-office-02.png, label="Pendant stem")
  → components/MediaCard.md (image=assets/mounting-gallery/hollowcore-2-0-lobby-02-desktop.png [mobile: hollowcore-2-0-lobby-02-mobile.png], label="Pendant cable")
  → components/MediaCard.md (image=assets/mounting-gallery/hollowcore-2-0-exterior-01-update.png [mobile: hollowcore-2-0-exterior-01.png], label="Post top")

## Data (text content, in order)
1. "Ceiling surface" — see components/MediaCard.md for full spec (this card already extracted there)
2. "Pendant stem"
3. "Pendant cable" (mobile layer casing "Pendant Cable" — same text)
4. "Post top" (mobile layer has double-space typo "Post  top" — same text)

## Tokens used
Inherited from components/MediaCard.md (color/white label, font/display type). No new tokens introduced by this block.

## States / variants seen
None beyond MediaCard's own — static stack, no hover/interaction observed.

## Breakpoints
desktop: cards stacked with 0 gap (verified: card y-offsets are exactly contiguous, e.g. 6110→6910→7710→8510, each +800)
mobile 390: cards stacked with 0 gap (verified: 3650→4150→4650→5150, each +500)
mobile image note: card 1 ("Ceiling surface") reuses the same source image mobile/desktop (per MediaCard.md). Card 2 ("Pendant stem") also reuses the same source image at both breakpoints (assets/mounting-gallery/hollowcore-2-0-office-02.png, hash-identical). Cards 3 and 4 use DIFFERENT source images per breakpoint (different Figma layers/crops) — separate mobile assets provided above.

## Assets
assets/mounting-gallery/hollowcore-2-0-office-02.png (card 2, shared desktop+mobile, 1928×1072 source)
assets/mounting-gallery/hollowcore-2-0-lobby-02-desktop.png (card 3 desktop, 1928×1072 source)
assets/mounting-gallery/hollowcore-2-0-lobby-02-mobile.png (card 3 mobile, 1928×1072 source)
assets/mounting-gallery/hollowcore-2-0-exterior-01-update.png (card 4 desktop, 1928×1072 source)
assets/mounting-gallery/hollowcore-2-0-exterior-01.png (card 4 mobile, 1928×1072 source)
card 1 assets: see components/MediaCard.md (assets/media-card/hollowcore-2-0-office-04.png)
