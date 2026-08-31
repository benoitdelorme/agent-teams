# home/resources
figma: fhdXQci2DTULtLlhVhg2I5 node 20:119 [mobile: title 20:33, table 20:6]     ref: ref/resources@800.png / ref/m-resources@800.png     extracted: 2026-08-24 hash n/a
size: 1440×720 desktop (title 9510→table end 10210, rel.) · 390×525 mobile     bg: raw #FFFFFF (no bg token defined in file)

## Layout (tree — indent = nesting; y offsets relative to block top = title top)
col  align center                                          ← block root
  text  h1  "Explore resources"  raw Work Sans ExtraLight 60px/60px uppercase  color raw #222  center  w 980  (differs from font/display 70px)
  gap ~90 (raw, title-bottom to table-top; measured on ref at 1440 — QA corrected from ~66)
  row (table, 5 stacked rows, full width 1440)
    vertical rule  x=280  h=550  1px  color raw hairline-gray (imgLine3/imgLineV asset, not sampled — nearest token color/border-subtle)
    vertical rule  x=1160  h=550  1px  same color as above
    col  (5× row, each h=110, hairline divider raw same color at top of each row + one final at bottom)
      row × 5  (label col starts x=380, CTA col starts x≈920–922)
        text  label  bold 20px/30px  color raw #222  (see Data for the 5 labels, in order)
        → components/CTA.md (label="Visit page" | "Download" ×4, per row — desktop pad/type per CTA.md desktop breakpoint)

## Data (rows top→bottom, label + CTA label)
A: "Family Page" → CTA "Visit page"
B: "Brochure" → CTA "Download"
C: "Spec Sheets" → CTA "Download"
D: "IES Files" → CTA "Download"
E: "Revit Files" → CTA "Download"

## Tokens used
color: none matched exactly (title/label #222 and hairlines are raw; CTA colors covered by components/CTA.md)     type: none matched (title raw, labels raw; CTA type per CTA.md)     space: row height 110 (raw), rule positions 280/1160 (raw)
raw (no token found): bg #FFFFFF, title/label text #222 (note: distinct from color/ink #101820), hairline divider color (unsampled, visually ≈ color/border-subtle #CECCCC), row height 110px, gap title→table ~90px

## States / variants seen
CTA instances in this block render dark text/border (#101820) on white row bg — opposite of components/CTA.md's documented white-on-dark treatment. Same pill/label structure, only the color context differs (light bg here vs dark nav/table bg elsewhere in that spec).
No hover/focus states (static file).

## Breakpoints
mobile 390 (title 20:33 + table 20:6, no vertical rules — desktop's two vertical rules are absent on mobile):
  title: Work Sans ExtraLight 40px/40px uppercase, raw color #101820 (note: mobile title color differs from desktop's #222)
  table: row h=80 (5 rows, total 400), label x=25 col starts, CTA col left≈254–260, label bold 16px/24px color raw #101820
  row order/labels: A "Product Page" (differs from desktop's "Family Page" — same CTA "Visit page"), B "Brochure", C "Spec Sheets", D "IES files", E "Revit files"
  hairline dividers same raw color as desktop, full width 390
  CTA per components/CTA.md mobile breakpoint (pad 20/14, label 12px/12px)

## Assets
none (hairlines and vertical rules are simple 1px line SVGs/structural, no icons or images in this block)
