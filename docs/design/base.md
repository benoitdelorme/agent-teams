# Base styles

Applies before any component. Composes tokens only.

- **Ground.** `body` is `--bg`, ink `--text`, type `--t-body` in `--font`, antialiased.
  The page never scrolls; each view owns its own scroll region.
- **Focus.** Every interactive element shows a visible ring: `outline: 2px solid
  --accent; outline-offset: 2px`. Never removed, never replaced by a colour change
  alone — the board is driven by keyboard as much as by pointer.
- **Selection.** `::selection` is `--accent` at 22% over the ground.
- **Scrollbars.** 8px, thumb `--border`, track transparent, thumb radius `--r-full`.
- **Editable text.** Inputs and textareas inherit the page face and never a browser
  default. A field at rest is `--card` on `--border`; on focus its border becomes
  `--accent` and nothing else moves — no shadow, no size change.
- **Reduced motion.** Under `prefers-reduced-motion: reduce`, `--fast` and `--enter`
  collapse to `0s` and the view transition becomes an instant swap.
- **Responsive floor.** Below 900px the ticket page drops its sidebar under the
  content column; the board scrolls horizontally with columns at a 232px floor.
