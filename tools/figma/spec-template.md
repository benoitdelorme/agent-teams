# Spec template — one block or one component, ≤ 60 lines, structure + tokens, no code

```
# <page>/<block>            (or: # Component: <Name>)
figma: <fileKey> node <id> [mobile <id>]     ref: ref/<block>@800.png     extracted: <date> hash <8hex>
size: 1440×720 (desktop) · full-bleed bg: bg/surface-2 (token) | raw #F4F4F5

## Layout (tree — indent = nesting; col/row = auto-layout direction)
col gap 64 pad 96/120  align center                    ← the block root
  row gap 24  align start  (2 cols: 1fr / 480 fixed)
    col gap 16                                         ← left column
      text  h1 "Pricing that scales"  type/display-lg  color text/primary  max-w 560
      text  p  "Start free, upgrade when…"  type/body-lg  color text/secondary
      row gap 12
        → components/Button.md (variant=primary, label="Start free")
        → components/Button.md (variant=ghost,   label="Talk to sales", icon=assets/hero/arrow.svg)
    image  assets/hero/dashboard.png  480×320  radius radius/lg  shadow shadow/md
  row gap 24 wrap                                      ← plan cards
    → components/Card.md × 3 (props: title=Free|Pro|Team, price=0|29|79, cta=…)  ← contents listed in Data

## Data (text content, in order; one line per repeated item)
Free: "$0", "For individuals", features: "1 project", "Community support"
Pro: …

## Tokens used
color: text/primary, text/secondary, bg/surface-2, brand/500     type: display-lg, body-lg, label-md     space: 12,16,24,64     radius: lg     shadow: md
raw (no token found): #F4F4F5 (bg), 18px/28px (p line-height)

## States / variants seen
Button hover (darker brand/600), Card "Popular" badge on Pro only

## Breakpoints (only if several node ids)
mobile 390: root pad 24/20, columns stack (col gap 32), cards col gap 16, image hidden

## Assets
assets/hero/dashboard.png (1×, 960×640 source), assets/hero/arrow.svg
```

Rules of thumb
- Every visible element is either a line here or covered by a `→ components/X.md` reference or a "× n" repeat. Nothing else.
- Tokens by name from `tokens.md`; unmatched → `raw` line. Sizes in px as designed; frontend maps to its scale.
- No Tailwind classes, no CSS, no React. Frontend chooses the implementation; the spec fixes the intent.
- A component spec has the same sections plus `## Props/variants` (name → values → what changes).
