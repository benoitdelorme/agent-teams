# D3 — auto-layout copies on Figma page `_autolayout` (2026-08-24)
Originals untouched. Every copy verified numerically: all nodes (containers + leaves) bbox delta ≤ 1px (max seen 0.17). Script: tools/figma/autolayout.js (patched: GROUP→FRAME step, container size restore, container-aware verification).

| block | original | copy | converted | groups→frames | skipped (reason) | max delta | vision |
|---|---|---|---|---|---|---|---|
| nav | 20:228 | copy 31:11 | converted 0 | g2f 1 | skipped: root MENU (mixed counter-axis alignment), Luminis-White 1 (overlap) | delta 0 | human: yes (nav row should be space-between/center) |
| hero | 20:201 | copy 37:29 (32:29 removed) | converted 1 (HE_Sign) | g2f 3 | skipped: root (mixed align), Mask group, 2 icon groups (irregular gaps) | delta 0.17 (27 nodes) | vision: faithful (qa/autolayout-hero.md) |
| intro | 20:196 | copy 34:7 | converted 0 | g2f 1 | skipped: root (mixed align), IMG (mask) | delta 0 | vision: n/a (identical) |
| gallery-family | 20:191 | copy 35:2 | converted 0 | g2f 0 | skipped: root group with mask (collage) | delta 0 | vision: n/a (identical) | human: masks block conversion |
| defining-center | 20:186 | copy 38:7 | converted 0 | g2f 1 | skipped: root (irregular gaps 41/36) | delta 0 | vision: n/a (identical) | human: gaps 41/36 are real → col with 2 gaps (frontend fine) |
| focal-statement | 20:181 | copy 39:6 | converted 1 (root) | g2f 1 | skipped: IMG (mask) | delta 0 | vision: faithful |
| closeup | 20:176 | copy 40:2 | converted 0 | g2f 0 | skipped: root group with mask | delta 0 | vision: n/a (identical) | human: mask |
| design-intent | 20:171 | copy 42:7 | converted 0 | g2f 1 | skipped: root (irregular gaps 41/36) | delta 0 | vision: n/a |
| mounting-gallery | 20:166/161/156/151 | copies 43:7, 43:13, 44:7, 45:7 | converted 4 (roots) | g2f 4 | skipped: VIDEO group with mask ×4 | delta 0 | vision: faithful (card 1) |
| resources | 20:119 | copy 46:34 | converted 0 | g2f 7 | skipped: root (gaps 66/110), TABLE (rotated child = vertical rules), rows A-E (overlap: hairline + label + CTA) | delta 0 | vision: n/a (identical) | human: table rows need manual autolayout |
| footer | 20:120 | none | blocked: root is a flat RECTANGLE (reference image), not convertible |
| m-nav | 20:110 | copy 48:10 | converted 0 | g2f 1 | skipped: root (mixed align), 48:6 (overlap) | delta 0 | vision: n/a | human: yes |
| m-hero | 20:84 | copy 49:28 | converted 2 (root, 49:8) | g2f 3 | skipped: Mask group, 2 icon groups (irregular gaps) | delta 0.1 (26 nodes) | vision: faithful |
| m-intro | 20:79 | copy 50:7 | converted 1 (root) | g2f 1 | skipped: IMG (mask) | delta 0 | vision: faithful (bg shows canvas grey: block has no own fill — not a defect) |
| m-gallery-family | 20:74 | copy 51:2 | converted 0 | g2f 0 | skipped: root group with mask | delta 0 | vision: n/a | human: mask |
| m-defining-center | 20:69 | copy 52:7 | converted 0 | g2f 1 | skipped: root (gaps 22/27) | delta 0 | vision: n/a |
| m-focal-statement | 20:64 | copy 53:6 | converted 1 (root) | g2f 1 | skipped: IMG (mask) | delta 0 | vision: pending |
| m-closeup (in focal) | 20:59 | copy 54:2 | converted 0 | g2f 0 | skipped: root group with mask | delta 0 | vision: n/a |
| m-design-intent | 20:54 | copy 55:7 | converted 0 | g2f 1 | skipped: root (gaps 12/36) | delta 0 | vision: n/a |
| m-mounting-gallery | 20:49/44/39/34 | copies 56:7, 57:7, 58:7, 59:7 | converted 4 (roots) | g2f 4 | skipped: VIDEO mask ×4 | delta 0 | vision: faithful (card 1, md5-identical) |
| m-resources | 20:4 | copy 60:32 | converted 1 (60:33) | g2f 7 | skipped: root (gaps 45/50), rows A-E (overlap) | delta 0 (30 nodes) | vision: pending |
| m-footer | 20:5 | none | blocked: RECTANGLE (flat image) |

## Needs human judgement (script refused, honestly)
- masks: gallery-family (both), closeup (both), hero "Mask group", intro/focal "IMG", MediaCard "VIDEO" ×8 — groups with a mask cannot get auto-layout; wrap the mask in a frame manually if wanted.
- nav (both): root children mixed alignment (logo left / CTA right) → needs a row with space-between; script only does uniform gaps.
- text bands (intro desktop, defining-center, design-intent, both bp): two different gaps (41/36…) → a column with 2 gaps; either accept absolute or set itemSpacing + a padding on the body.
- resources table (both): rows = hairline + label + CTA overlapping → manual row auto-layout; vertical rules are rotated lines.
- footer (both): flat RECTANGLE reference image — not convertible.
