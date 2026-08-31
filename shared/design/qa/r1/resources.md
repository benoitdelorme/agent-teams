# QA home/resources — 2026-08-24
A = ref/resources@800.png, ref/m-resources@800.png · B = qa/resources.png, qa/m-resources.png

## desktop 1440 (ref 800 scale ×1.8)
med  gap title→table — expected: ~90px between title glyph bottom and first divider (51px@800 in A; spec says ~66) / got: ~72px (40px@800) — table sits ~20px too close to the title
low  space above title — expected: n/a (A is cropped at title top) / got: ~80px of white above the title; not judged, verify against page rhythm
Checked and matching: title size/weight/tracking/width (Work Sans ExtraLight, 336px@800 wide, centered), 5 rows × 110px, dividers at every row + final, vertical rules at x=280 / x≈1160 spanning table only, label x=380 bold 20px, labels "Family Page/Brochure/Spec Sheets/IES Files/Revit Files", CTA labels "VISIT PAGE" + 4× "DOWNLOAD", CTA on-light variant (ink text + 1px ink border, no fill, pill radius, 50px tall, x≈920), text color #222-ish.

## mobile 390 (table only vs ref; title judged against spec)
faithful
Checked and matching: 5 rows × 80px, full-width hairlines top + bottom, no vertical rules, label x=25 bold 16px, labels "Product Page/Brochure/Spec Sheets/IES files/Revit files", pill CTAs ~40px tall right-aligned at x≈254–260 and vertically centered (pill width within 3px of A), label 12px uppercase, ink text/border on white. Title (not in ref): 2 lines "EXPLORE / RESOURCES", ~40px/40px ExtraLight uppercase, centered, ink color — consistent with spec.
