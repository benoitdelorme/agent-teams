# Column

One workflow state. Five exist and the set is closed: backlog, todo, doing, qa, done.

**Composes:** `--color-ink-900`, `--color-ink-750`, `--radius-col`, `text-[12.5px]`, `text-[11px]`, `--color-mute`,
`--color-signal`, `--color-ink-600`, a colour transition.

**Anatomy.** Head — name in sentence case at `text-[12.5px]` weight 600 in `--color-mute`, a
count chip, and (backlog only) an add control. Body — scrollable list, gap `--s2`.

**States**

| state | treatment |
|---|---|
| rest | `--color-ink-900` on `--color-ink-750` |
| drop target | border `--color-signal`, ground lifts one step; a colour transition |
| empty | a dashed `--color-ink-700` well at `--radius-card` carrying one sentence of direction, not a dash |

**Rules.** The column name is never set in capitals. `backlog` is the only column that
can create a ticket — it is the human's column, and the add control says so by being
the only one present.
