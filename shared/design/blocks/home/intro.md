# home/intro
figma: fhdXQci2DTULtLlhVhg2I5 node 20:196 [mobile 20:79]     ref: ref/intro@800.png (desktop) / ref/m-intro@800.png (mobile)     extracted: 2026-08-24 hash 4bc64bad/cb188633
size: 1440×550 (desktop) · 390×420 (mobile) · full-bleed bg: color/white (raw #FFFFFF) (white band, dark text — confirmed by lead)

## Layout (tree — indent = nesting)
col gap 40 (space/title-body-gap)  align center  justify center (content vertically centered in block)
  text  h  "The center of attention"  font/display  color color/ink  uppercase  text-align center  max-w 1180
  text  p  "A new indoor/outdoor luminaire family designed to create hierarchy in architectural space. Hollowcore Element draws focus, reinforcing composition, and shaping atmosphere with intention."  font/body  color color/text-secondary  text-align center  max-w 780

## Data (text content)
Title: "The center of attention" (rendered uppercase; source case as typed above)
Body: "A new indoor/outdoor luminaire family designed to create hierarchy in architectural space. Hollowcore Element draws focus, reinforcing composition, and shaping atmosphere with intention."

## Tokens used
color: color/ink, color/text-secondary, color/white     type: font/display, font/body     space: space/title-body-gap (desktop only, see Breakpoints)
raw (no token found): none on desktop

## States / variants seen
None — static text block, no interactive elements.

## Breakpoints (mobile 390×420, node 20:79)
- root: content vertically centered, ~100px top/bottom padding, pad-x so text max-w 340 (25px side margin)
- title: font raw 50px/50px (desktop font/display is 70px/70px — mobile is a scaled override, not a separate token), still uppercase, color/ink, max-w 340
- body: font raw 14px/21px (desktop font/body is 16px/24px — mobile override), color/text-secondary, max-w 340
- gap title→body: raw ~16px (desktop uses space/title-body-gap=40px; mobile is smaller, no matching token)

## Assets
None — background is a flat white rect (Rectangle 2, fill white, full-bleed), no image/svg content to extract.

## Note
This block, `defining-center`, and `design-intent` share the same layout structure (per MANIFEST). They will be extracted separately; when specced, check they reference this file's layout pattern rather than duplicating it, and confirm whether their bg color also deviates from the "dark band" description.
