# Team pill

Live state of one crew member, in the header. Fully round (`rounded-full`).

**Composes:** `--color-ink-850`, `--color-ink-700`, `--color-mute`, `--color-good`, `--color-signal`, `--color-alert`, `--color-faint`.

**Anatomy.** A 7px dot, then the team's title.

| state | dot |
|---|---|
| working | `--color-good`, with a 6px glow |
| idle | `--color-signal`, no glow |
| gone | `--color-alert`, no glow |
| unknown | `--color-faint` |

**Rules.** The dot carries the state and the title carries the identity; the pill's own
ground never changes. Its tooltip gives the purpose and the last-seen time in words.
