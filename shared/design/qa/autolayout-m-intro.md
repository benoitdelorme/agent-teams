# autolayout m-intro — original 20:79 vs copy 50:7 (page _autolayout)
mode: autolayout   A: ref/m-intro@800.png   B: qa/autolayout-m-intro@800.png (390x420, both)

VERDICT: changed (layout faithful, background color differs)

med background — expected: color/white #FFFFFF (Rectangle 2 fill, per spec) / got: #F5F5F5 light grey across the whole frame

Everything else identical: title (2 lines, uppercase, same position/size), body (5 lines, same wrap), title→body gap, vertical centering, side margins — 0 px text diff at 8% fuzz.
Likely cause: the copy's root frame fill was set to grey (or the white Rectangle 2 was dropped/hidden and the frame default fill shows) during the re-layout.
