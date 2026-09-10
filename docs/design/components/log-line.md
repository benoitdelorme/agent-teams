# Log line

One entry of a ticket's `## Log`. The log is a transcript of a crew at work, and this
component is where the system's semantic rule is most visible: cool is an agent working,
warm is something involving you.

**Composes:** `text-[12.5px]`, `text-[11px]`, `--color-faint`, `--color-paper`, `--color-signal`, `--color-good`, `--color-alert`,
`--color-you`, `--radius-card`, `--color-ink-900`.

**Anatomy.** Time in mono `text-[11px]` `--color-faint`, fixed column, then the text.

**Speaker colouring** — the marker word only, never the whole line. Cool markers are
ambient; a warm marker is the thing you are scanning for:

| marker | ink | speaker |
|---|---|---|
| `TASK`, `ASK`, `CONTRACT`, `NEW` | `--color-signal` | agent |
| `DONE`, `ANSWER` | `--color-good` | agent |
| `BLOCKED` | `--color-alert` | agent |
| `human:`, `COMMENT` | `--color-you` | you |

**States.** Rest — no ground. Hover — `--color-ink-850` ground at `--radius-card`, so a long log can
be tracked with the pointer. The well itself is `--color-ink-900`, scrolls, and pins to the
newest line unless the reader has scrolled away from the end.

**Rules.** A line is never truncated. The marker is the only coloured run in the line.
