# Component: CTA
figma: fhdXQci2DTULtLlhVhg2I5 node 20:230 [mobile 20:112]     ref: ref/CTA@800.png     extracted: 2026-08-24 hash n/a

## Layout (tree — indent = nesting)
row (pill button, border only, no fill)  pad space/pill-pad-x / space/pill-pad-y  radius radius/pill  border 1px color/white
  text  label  "View resources"  font/label  color color/white  uppercase  center  nowrap

## Data (text content)
Label is dynamic (button text), sample: "View resources"

## Tokens used
color: color/white (text + border)     type: font/label     space: pill-pad-x (30px desktop / 20px mobile), pill-pad-y (18px desktop / 14px mobile)     radius: radius/pill
raw (no token found): mobile label size 12px/12px line-height (desktop uses font/label 14px/14px — mobile is a smaller override, not a separate token)

## States / variants seen
Only one visual treatment observed across both nodes checked (20:230 desktop, 20:112 mobile): white text + white 1px border, no fill, on dark bg (color/ink nav/table background). No light-bg (dark-text) variant present in either sampled instance — not a Figma component/variant set, just a repeated pill-button layer used 7× (nav ×2 breakpoints, "Explore resources" table both breakpoints).
Not observed: hover/active/disabled/focus states (static design file).

## Variants (context override, same component)
on-light (home/resources rows): text + border color/ink on white bg — see blocks/home/resources.md. on-dark (nav): color/white.

## Breakpoints
desktop (20:230): pad 30px/18px, label font/label 14px/14px
mobile (20:112): pad 20px/14px, label 12px/12px (raw, smaller than font/label)

## Assets
none (text-only pill, no icon/SVG)
