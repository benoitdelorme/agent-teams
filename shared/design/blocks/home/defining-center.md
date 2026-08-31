---
# home/defining-center
figma: fhdXQci2DTULtLlhVhg2I5 node 20:186 [mobile 20:69]     ref: ref/defining-center@800.png (desktop) / ref/m-defining-center@800.png (mobile)     extracted: 2026-08-24 hash 20186/2069
size: 1440×620 (desktop) · 390×470 (mobile) · full-bleed bg: raw #616869 — same hex as `color/text-secondary`, but used here as a solid background fill, not as text color. Genuinely dark, unlike home/intro (see [[home-intro]] — that block's "dark band" bg is actually white; this one is the real dark band).

## Layout (tree — same structure/geometry as home/intro, see [[home-intro]]; differs in bg color and adds a 3rd text line)
col gap 41 (title→body) / 36 (body→tagline)  align center  justify center (content vertically centered in block)
  text  h  "Defining the Center"  font/display  color color/white  uppercase  text-align center  max-w 1180
  text  p  "Hollowcore Element was designed to be that center. Beyond decoration, it serves as a design tool that guides focus, enhances architectural character, and transforms the feeling of a space."  font/body  color color/border-subtle (as text)  text-align center  max-w 780
  text  tagline  "Where attention settles, a space finds its balance."  raw Work Sans Bold 20px/24px, tracking 0.6px, uppercase  color color/ink  text-align center  max-w 780

## Data (text content, in order)
Title: "Defining the Center" (rendered uppercase)
Body: "Hollowcore Element was designed to be that center. Beyond decoration, it serves as a design tool that guides focus, enhances architectural character, and transforms the feeling of a space."
Tagline: "Where attention settles, a space finds its balance." (rendered uppercase)

## Tokens used
color: color/white, color/ink     type: font/display, font/body
raw (no token found): #616869 (bg — matches color/text-secondary hex but different role), Work Sans Bold 20px/24px tracking 0.6px (tagline — no bold weight token exists yet)

## States / variants seen
None — static text block, no interactive elements.

## Breakpoints (mobile 390×470, node 20:69)
- root: bg #616869, content vertically centered, pad-x so text max-w 340, col gap 22 (title→body) / 27 (body→tagline)
- title: font raw 50px/50px (desktop font/display is 70px/70px — mobile scaled override), uppercase, color/white, max-w 340
- body: font raw 14px/21px (desktop font/body is 16px/24px — mobile override), color color/border-subtle (as text), max-w 340
- tagline: font raw Work Sans Bold 18px/22px tracking 0.54px (desktop is 20px/24px tracking 0.6px), color/ink, max-w 340

## Assets
None — background is a flat #616869 rect, no image/svg content.
