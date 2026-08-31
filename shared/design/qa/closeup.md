# qa: home/closeup — round 2 (desktop 1440, ref/closeup@800.png vs qa/closeup.png)

faithful

r1 diffs checked:
- photo stack (cable-hand): fixed — shade x 117→685 / y 197→385 in A, x 117→684 / y 196→384 in B (800 scale, ≤ 1 px)
- block height / next block intrusion: fixed — B is 533 px tall (A 534), bottom rows show the dark photo strip, no foreign block
- right edge: fixed — dark strip (≈7 px at 800 scale ≈ 11 px at 1440) present at the right edge in B, same rgb(44,45,50) as A
- background layers: fixed — dark strips at right and bottom edges prove stem-bg-dark / surface-x2 render behind cable-hand
- focal-statement heading overlap: not judgeable here (A has no heading); "COMPOSED." glyph bottom now ≈ 112 px into the block, consistent with a 133 px text-box bottom minus descent — confirm in focal-statement QA
