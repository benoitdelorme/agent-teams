# autolayout m-resources — 20:4 (original) vs 60:32 (_autolayout copy)

VERDICT: faithful

A: ref/m-resources-full@800.png  B: qa/autolayout-m-resources@800.png (both 390×1490 canvas)
- Title "EXPLORE RESOURCES": same size, weight, centering, 2-line wrap.
- Table: 5 rows (Product Page/Brochure/Spec Sheets/IES files/Revit files), same order, row height, dividers, labels left, pill buttons right, same pill size and labels (VISIT PAGE / DOWNLOAD ×4).
- Footer (included in node 20:4): logo, address, Acuity mark, copyright, 2-column link lists, legal links — identical position and spacing.
- Pixel diff (fuzz 10%): 801/168000 px, all in a thin band at the bottom edge of the frame — copy height differs by a few canvas px (hug rounding). Low, not a layout change.
