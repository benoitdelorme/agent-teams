# home/nav
figma: fhdXQci2DTULtLlhVhg2I5 node 20:228 (desktop) [mobile 20:110]     ref: ref/nav@800.png / ref/m-nav@800.png     extracted: 2026-08-24 hash n/a
size: 1440×80 (desktop) · 390×70 (mobile) · full-bleed bg: color/ink (token, raw #101820)
position hint: root node is a fixed 1440×80 bg rect (20:229) at top:0 left:0, full page width, no scroll offset in the sampled frame — consistent with sticky/fixed top bar, but no overlap-with-hero or position:fixed property is present in the static Figma node itself. Flag as sticky candidate for frontend, not confirmed by Figma data.

## Layout (tree — indent = nesting; positions given, no auto-layout present in source — all children absolutely positioned)
row (bar) w full  h space/nav-height  bg color/ink                 ← root, height fixed to space/nav-height (80px desktop)
  image  assets/nav/luminis-logo.svg  "Luminis" wordmark+mark  124×26 (desktop) / 91×19 (mobile)
    pos desktop: left 50px, top 27px (vertically centered in 80px bar)
    pos mobile:  left 25px, top 25.5px (vertically centered in 70px bar)
  → components/CTA.md (label="View resources")
    pos desktop: right-aligned, left 1205px top 15px (i.e. right edge 1440-1205-pill_width≈1440-30px margin), pill pad space/pill-pad-x/space/pill-pad-y
    pos mobile:  left 218px top 15px, pill pad 20px/14px (component's mobile override)

## Data (text content)
Logo: "LUMINIS" wordmark (SVG asset, includes small trademark/registered mark per screenshot)
CTA label: "View resources" (see components/CTA.md — dynamic)

## Tokens used
color: color/ink (bg, raw #101820)     space: space/nav-height (80px desktop bar height; mobile bar height 70px is a raw override — no token)
raw (no token found): mobile bar height 70px, logo positions (left/top px above — one-off placement, not tokenized)

## States / variants seen
Only static state sampled (no hover/scroll/sticky behavior visible in Figma). No variant set — single treatment at each breakpoint.

## Breakpoints
desktop (20:228, 1440×80): logo left 50/top 27, CTA left 1205/top 15
mobile (20:110, 390×70): logo left 25/top 25.5, CTA left 218/top 15

## Assets
assets/nav/luminis-logo.svg (single asset used at both breakpoints, scaled by CSS: 124×26 desktop, 91×19 mobile)
