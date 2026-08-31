# qa: nav — round 3 (ref/nav@800.png vs qa/nav.png · ref/m-nav@800.png vs qa/m-nav.png)

## desktop (1440)
faithful
- CTA label weight: now matching. Weight 400 reads as the ref at 4x; glyph extents identical (x26-94 @800 in both), pill bounds identical (x669-771, y8-35). Residual: label ink +27% at 0.56x scale — browser rasterization at ~5px cap height, not a weight step (a 500 would widen the run). No action.
- low nav bottom edge — expected: none (mobile ref has none) / got: n/a — ref PNG's last row is a 1px light line (mean lum 139), most likely crop bleed from the section below; B has none. Ignore unless the Figma nav has a real bottom rule.

## mobile (390)
faithful
- CTA label weight: matching. Ink +12% vs ref (r2: +40%), mean stroke run 2.41 vs 2.14 px, identical glyph extents (x38-143 y31-38) — within renderer gamma. Pill x216-364 vs ref x218-364 (unchanged since r1, within 2px). Logo bounds identical.
