# home/hero
figma: fhdXQci2DTULtLlhVhg2I5 node 20:201 [mobile 20:84]     ref: ref/hero@800.png (desktop), ref/m-hero@800.png (mobile)     extracted: 2026-08-24 hash 20201f01

size: 1440×880 (desktop), 390×450 (mobile) · full-bleed, no side padding

## Layout (tree — indent = nesting; absolute-positioned block, no auto-layout)
block  h880 (full-bleed, sits below nav space/nav-height)
  layer  3 stacked photos, each clipped/masked to the block's 1440×880 rect at a slightly different pan offset (parallax-style crop), full-bleed cover
    image  assets/hero/photo-ceiling-lights-row.png   (masked crop 1583×880 offset left -72,72 top 0)
    image  assets/hero/photo-pendant-window.png       (masked crop 1724×958 offset left -89,89 top 78, appears above/behind the others)
    image  assets/hero/photo-exterior-post-lamp.png   (masked crop 1564×880 offset left -123,123 top 0, topmost — visible in final render)
  logo  assets/hero/he-sign-wordmark.svg + assets/hero/he-sign-subtitle.svg   pos left 530 top 738 (desktop) / left 82 top 397 (mobile)  size 400×122 (desktop) / 240×73 (mobile)
    "HOLLOWCORE" (wordmark, bold, color/white)
    "ELEMENT" (subtitle, lighter/thin weight, color/white at reduced opacity)
  icon  scroll hint  assets/hero/scroll-hint.jpg  pos right, top 796  size 25×114 — desktop only, blend mode "lighten", not present on mobile

## Data (text content)
"HOLLOWCORE" / "ELEMENT" — product name lockup, rendered as vector wordmark (not live text)
scroll hint icon reads "scroll ↓" (vertical arrow, desktop only)

## Tokens used
color: color/white (logo text)
raw (no token found): none — mask offsets/photo positions are raw layout numbers, not design tokens

## States / variants seen
None — static hero, no visible hover/interaction states on this node.

## Breakpoints (only if several node ids)
mobile 390×450: same 3-photo stack, tighter mask crops (390×450 window instead of 1440×880); mask top offset 66-70px vs 0-80px desktop; logo lockup scaled to 240×73, repositioned to left 82 top 397; scroll-hint icon removed entirely on mobile.

## Assets
assets/hero/photo-ceiling-lights-row.png (1928×1072 source)
assets/hero/photo-pendant-window.png (1928×1072 source)
assets/hero/photo-exterior-post-lamp.png (1920×1080 source)
assets/hero/he-sign-wordmark.svg (400×37)
assets/hero/he-sign-subtitle.svg (400×53)
assets/hero/scroll-hint.jpg (50×227 source, desktop only)
