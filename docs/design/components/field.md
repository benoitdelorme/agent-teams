# Field

Any editable value: single-line, multi-line, or select.

**Composes:** `--color-ink-850`, `--color-ink-700`, `--color-signal`, `--radius-field`, `text-sm`, `text-[12.5px]`,
`--color-faint`, `--color-mute`.

**Anatomy.** Label in sentence case at `text-[12.5px]` in `--color-mute`, then the control. The
label sits above and is never in capitals.

**States**

| state | treatment |
|---|---|
| rest | `--color-ink-850` on `--color-ink-700` |
| hover | border lightens one step |
| focus | border `--color-signal`; nothing else changes |
| saving | border `--color-ink-600`, control stays live |
| invalid | border `--color-alert` and one sentence beneath saying what to do |

**Sizes.** `compact` — one line, `--s2` padding, for the sidebar. `prose` — multi-line,
auto-growing from its content, minimum 6 lines, for description and criteria. A `prose`
field never shows a resize grip: it grows on its own.

**Rules.** A field commits on blur, never on every keystroke. A field being edited is
never overwritten by an incoming update — remote changes wait for blur.
