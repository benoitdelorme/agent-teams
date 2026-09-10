# Action

Anything that does something when pressed. Fully round (`rounded-full`).

| variant | rest | hover | for |
|---|---|---|---|
| `primary` | `--color-signal` ground, `--color-signal-ink` ink | ground lightens | the one action a view exists for |
| `quiet` | transparent, `--color-mute` ink, `--color-ink-700` edge | ink `--color-paper`, edge lightens | everything else |
| `bare` | transparent, `--color-faint` ink, no edge | ink `--color-paper` | close, back, add |
| `danger` | transparent, `--color-faint` ink | ink `--color-alert`, edge `--color-alert` at 35% | destroys a ticket |

**Rules.** One `primary` per view at most. A label says what happens — *Add note*, not
*Submit* — and keeps that word through the whole flow, including the toast that follows.
No arrow is appended to a label. `danger` never starts as red: it earns its colour on
approach, so a mis-aimed pointer is not a scare.
