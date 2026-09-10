# SCR-001 — Board

The default view. Answers one question at a glance: *what is the crew doing, and what
is waiting on me?*

**Composes:** column, card, chip, team-pill, field (`compact`, the filter), action
(`bare`, add), toast.

```
┌────────────────────────────────────────────────────────────────────┐
│ Board  <plan title>        [filter…]  ● gestion ● server ● client ●│
├──────────┬──────────┬──────────┬──────────┬────────────────────────┤
│ Backlog 3│ Todo   1 │ Doing  2 │ Qa     0 │ Done                 7 │
│      [+] │          │          │          │                        │
│ ╭──────╮ │ ╭──────╮ │ ╭──────╮ │          │ ╭──────╮               │
│ │T9    │ │ │T7    │ │ │T4 srv│ │   empty  │ │T1    │               │
│ │title │ │ │title │ │ │title │ │   well   │ │title │               │
│ ╰──────╯ │ ╰──────╯ │ ╰──────╯ │          │ ╰──────╯               │
└──────────┴──────────┴──────────┴──────────┴────────────────────────┘
```

- Five columns, equal width, 232px floor, horizontal scroll below that.
- **Backlog is yours.** It is the only column with an add control, and the only one
  `gestion` is told never to read. The interface says this by what it offers, not by a
  notice.
- Dragging a card to **Todo** is the one gesture that wakes the crew. Its toast names
  the consequence: *T7 → Todo — gestion notified.*
- A card opens SCR-002. A drag never opens it.
- Empty column: one sentence of direction, sentence case. Backlog's is an invitation.
- The connection dot sits last in the header, `--ok` when the stream is live.
