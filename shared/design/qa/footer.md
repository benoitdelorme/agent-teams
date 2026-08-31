# qa/footer — 2026-08-24

## desktop (ref/footer@800.png vs qa/footer.png, both 800×262)
faithful — logo, address block, 2 link columns, column dividers, Acuity logo + copyright line, bottom legal bar (SITE TERMS … FR) all match in position, size, weight and color; no diff above jitter.

## mobile (ref/m-footer@800.png 341×800 vs qa/m-footer.png 390×915, normalised ×0.874)
low  link-columns box bottom border — expected: ~43 px below GOVERNANCE (bottom bar links start ~66 px under it) / got: ~54 px below GOVERNANCE, ~57 px above SITE TERMS (border sits ~10 px lower; text positions themselves match)
otherwise faithful — logo rule + wordmark, address, Acuity logo, copyright wrap ("…ALL RIGHTS / RESERVED."), top divider, 2 columns with vertical separator, "X FORMERLY / TWITTER" wrap, bottom links wrap ("…MY PERSONAL / INFORMATION") all match.
