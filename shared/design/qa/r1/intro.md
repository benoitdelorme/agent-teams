# qa: home/intro — 2026-08-24
ref/intro@800.png vs qa/intro.png · ref/m-intro@800.png vs qa/m-intro.png (mobile PNGs are 390 wide, compared 1:1)

## Desktop (1440, measured at 800 → ×1.8)
med  gap title→body — expected: body top 31px below title cap-bottom @800 (≈56px real, token space/title-body-gap 40 + line slack) / got: 24px @800 (≈43px real); body block sits ~13px too high, title position itself is exact (rows 118–144 in both)
low  body line-height — expected: two lines with visible 5px inter-line gap @800 (16/24) / got: lines nearly touching (pitch ~1–2px tighter @800, ≈2–3px real); text size looks equal
low  top edge — expected: pure white / got: 1px full-width dark hairline at row 0 (border-top or bleed from the block above; verify it is not a border on this section)
Structure, text content, uppercase, centering (x 152–645 identical), title size/weight, body color: match.

## Mobile (390)
low  gap title→body — expected: 33px between title bottom and body top / got: 29px (body and all five lines 4px higher; line pitch 21px identical)
Structure, wrapping (same 2 title lines, 5 body lines), x-margins (31px), title size, colors, block height (420 vs 421): match.
