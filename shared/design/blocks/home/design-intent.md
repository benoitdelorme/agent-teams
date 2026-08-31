# home/design-intent
figma: fhdXQci2DTULtLlhVhg2I5 node 20:171 [mobile 20:54]     ref: ref/design-intent@800.png (desktop) / ref/m-design-intent@800.png (mobile)     extracted: 2026-08-24 hash 20171/2054
size: 1440×620 (desktop) · 390×450 (mobile) · full-bleed bg: color/ink (raw #101820) — genuinely dark, same geometry family as blocks/home/defining-center.md but different bg token (that block uses raw #616869, this one uses color/ink).

## Layout (tree — same structure/geometry as home/defining-center, see blocks/home/defining-center.md; differs in bg color, text content, and body/tagline text-color roles)
col gap 41 (title→body) / 36 (body→tagline)  align center  justify center (content vertically centered in block)
  text  h  "Design Intent"  font/display  color color/white  uppercase  text-align center  max-w 1180
  text  p  "Hollowcore Element is conceived with a deliberately restrained architectural presence, clean, composed, and free of visual noise."  font/body  color color/border-subtle (as text) [raw #CECCCC]  text-align center  max-w 580
  text  tagline  "built around a luminous form that is meant to be seen."  raw Work Sans Bold 20px/24px, tracking 0.6px, uppercase  color color/text-secondary (raw #616869)  text-align center  max-w 780

## Data (text content, in order)
Title: "Design Intent" (rendered uppercase)
Body: "Hollowcore Element is conceived with a deliberately restrained architectural presence, clean, composed, and free of visual noise."
Tagline: "built around a luminous form that is meant to be seen." (rendered uppercase)

## Tokens used
color: color/ink (bg), color/white, color/border-subtle (as text), color/text-secondary     type: font/display, font/body
raw (no token found): Work Sans Bold 20px/24px tracking 0.6px (tagline — no bold weight token exists yet, same gap as blocks/home/defining-center.md)

## States / variants seen
None — static text block, no interactive elements.

## Breakpoints (mobile 390×450, node 20:54)
- root: bg color/ink, content vertically centered, pad-x so text max-w 340/335, col gap 12 (title→body) / 36 (body→tagline)
- title: font raw 50px/50px (desktop font/display is 70px/70px — mobile scaled override), uppercase, color/white, max-w 335
- body: font raw 14px/21px (desktop font/body is 16px/24px — mobile override), color color/border-subtle (as text), max-w 340
- tagline: font raw Work Sans Bold 18px/22px tracking 0.54px (desktop is 20px/24px tracking 0.6px), color color/text-secondary, max-w 340

## Assets
None — background is a flat color/ink (#101820) rect, no image/svg content.
