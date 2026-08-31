# qa/defining-center — app vs ref (2026-08-24)

## desktop (1440, judged on 800px renders, ×1.8 to 1440)
med body→tagline gap — expected: ~54px (ref: body sits visually midway between title and tagline) / got: ~25px (tagline hugs the paragraph)
med title→body gap — expected: ~50px (ref) / got: ~85px (paragraph pushed down ~27px at 1440 scale)
Everything else faithful: bg #616869, title size/weight/tracking/uppercase, body size/line-height/color/max-w (2 lines, same wrap), tagline bold/uppercase/ink, block height, horizontal centering, text content.

## mobile (390)
med body→tagline gap — expected: ~48px (ref: body bottom 293 → tagline top 341) / got: ~26px (310 → 336)
med title→body gap — expected: ~54px (ref: title bottom 176 → body top 230) / got: ~67px (body starts at 243)
low body line-height — expected: 21px (spec 14/21, ref 4 lines over 63px) / got: ~22px (4 lines over 67px)
Everything else faithful: bg, title 2-line wrap and size, body wrap (same 4 line breaks), tagline 2-line wrap, block height 470, text content.

## note
Spec line 7 states gaps "~90 (title→body) / ~16 (body→tagline)" — the app matches those numbers, but the Figma ref shows ~50/~54 (near-equal). The spec gap values look wrong (probably measured on text-box edges incl. line-height slack); re-extract or trust the ref.
