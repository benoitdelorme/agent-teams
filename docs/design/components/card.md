# Card

A ticket at rest in a column. It is a drag handle, a link to the ticket page, and a
status summary — in that order of frequency.

**Composes:** `--color-ink-850`, `--color-ink-800`, `--color-ink-700`, `--radius-card`, `text-[13.5px]`, `text-[11px]`,
`--color-alert`, `--color-faint`, a colour transition.

**Anatomy.** Identifier chip · optional Jira chip · optional team badge, then the title
(2 lines max, wraps, never truncated mid-word), then a footer carrying the relative
update time and, when blocked, the word.

**States**

| state | treatment |
|---|---|
| rest | `--color-ink-850` on `--color-ink-700`, `--radius-card` |
| hover | ground `--color-ink-800`, border lightens one step; a colour transition |
| focus | base focus ring; does not replace hover |
| pressed / dragging | opacity .3, stays in place; the ghost carries the pointer |
| blocked | 3px `--color-alert` left bar, inset so the radius is preserved, plus the word in the footer |
| filtered out | removed from flow, not dimmed |

**Rules.** The card never carries a shadow at rest — shadow is reserved for the drag
ghost, where it means *lifted*. Two cards never differ by radius.
