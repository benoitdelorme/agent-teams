# qa/defining-center — round 3 (2026-08-24; frontend lh 24/21, gaps 41-36 / 22-27, heights 620/470)

## desktop (1440, measured on 800px renders — ink row bands, ×1.8 to 1440)
med title→body gap — expected: 31px ink gap @800 (~56 @1440; ref 144→175) / got: 26 @800 (~47; 144→170), still ~9px tight (r2 was 25, so +1 only)
low body→tagline gap — expected: 29 @800 (~52; ref 196→225) / got: 26 @800 (~47; 191→217), ~5px tight (r2 was 24)
Content block 107 vs 114 @800 (~13px shorter at 1440), still vertically centered. Title bottom edge identical (y144), title x-extent 187–611 vs 188–612, body 2-line wrap + 5px pitch, tagline size/weight, bg #616869, block height 344 vs 345, text content: all faithful.
Note: the r2 residual is almost unchanged — the lh change did not move the gaps; browser line-box slack of ~5px @800 (~9 @1440) above the body remains. If a further pass is wanted, add ~9px to the title→body gap (41→50) and ~5px to body→tagline (36→41) as a compensating override; otherwise acceptable as low-visibility.

## mobile (390, 1:1)
faithful — block height 470 (r2 +7 fixed); title rows 105–139/155–189 vs ref 108–142/158–192 (3px high, at jitter threshold), body rows 224–299 vs 225–300 (1px), tagline rows 335–368 identical, title→body gap 35 vs 33, body→tagline 36 vs 35, x-extent 29–357 identical, all wraps (2/4/2 lines) and text content identical.
