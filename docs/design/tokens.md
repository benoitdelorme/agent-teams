# Tokens

Declared in one place: the `@theme` block of `tools/board/index.html`. Tailwind v4 emits
each as a CSS custom property and generates the matching utilities, so `--color-signal`
is both `var(--color-signal)` and `text-signal` / `bg-signal` / `border-signal`.

A component contract may only compose these. Adding a token is a change to the
foundation, decided here and deliberately — never as the side effect of one screen.

`derived` = read out of `tools/board/index.html` as it stood before this system.
`filled-in` = proposed here, with no prior value in the code.

## Ground — cool ink with a violet cast

Two grounds were tried. The first was warm brown-black under an orange accent; it read
muddy, because accent and ground sat in the same hue family with too little separation.
This ground is cool and slightly violet: deep without collapsing to flat black, and far
enough from every accent below that each one reads at chip size. All filled-in.

| token | value | role |
|---|---|---|
| `--color-ink-950` | `#0D0C13` | page |
| `--color-ink-900` | `#15141D` | column, sidebar, log well |
| `--color-ink-850` | `#1C1B26` | card, field, chip |
| `--color-ink-800` | `#252331` | card under the pointer |
| `--color-ink-750` | `#201E2B` | an edge that should be felt, not seen |
| `--color-ink-700` | `#322F42` | an edge that should be seen |
| `--color-ink-600` | `#413D55` | an edge under the pointer |

## Ink

| token | value | role | source |
|---|---|---|---|
| `--color-paper` | `#EFEDF7` | primary | filled-in (was `#e7e9ec`) |
| `--color-mute` | `#A29EBB` | secondary | filled-in (was `#8b929c`) |
| `--color-faint` | `#6D6889` | tertiary, placeholders | filled-in (was `#5a616c`) |

## Who is speaking

The board's whole job is showing a human what a crew of agents is doing. **Cool hues
carry agents at work — ambient, not asking for you. Warm hues mark anything a person is
involved in: your own input, and an agent that has stopped and needs you.**

You scan a log looking for what concerns you. What concerns you is warm.

| token | value | speaker | role |
|---|---|---|---|
| `--color-signal` | `#8B9DFF` | agent, working | interactive, focus ring, `TASK` `ASK` `CONTRACT` `NEW` |
| `--color-signal-ink` | `#0B0D1F` | — | ink on a filled `signal` surface |
| `--color-good` | `#4FD6A9` | agent, finished | `DONE` `ANSWER`, live stream |
| `--color-alert` | `#FF6B81` | agent, stopped | blocked — and nothing else |
| `--color-you` | `#F2B366` | you | `human:`, `COMMENT`, the Jira keys you filed |

Blocked is signalled by hue step *and* form — a 3px left bar plus the word — never by
hue alone: at chip size a hue step is not enough on its own.

## Radius — a hierarchy, not a single value

One radius on everything regardless of hierarchy is the generic default. Roundness
descends with the element's weight in the page.

| token | value | applies to |
|---|---|---|
| `--radius-shell` | `24px` | ticket page shell |
| `--radius-col` | `20px` | column |
| `--radius-card` | `16px` | card, log well, toast |
| `--radius-field` | `14px` | input, textarea, select |
| `rounded-full` | — | chip, badge, pill, button |

## Type

| token | value | source |
|---|---|---|
| `--font-sans` | `Instrument Sans`, then the system stack | filled-in (was `Inter`) |
| `--font-mono` | `JetBrains Mono`, `SF Mono`, `ui-monospace` | derived |

Instrument Sans is a contemporary grotesque with enough character to carry a 32px
title, and it is not the face every generated interface reaches for. Mono is reserved
for **identifiers only** — `T7`, a Jira key, a file path: a value you might read aloud,
compare, or type. Never for prose labels.

Sizes are Tailwind's scale plus four arbitrary values, each used once: `32px` (ticket
title), `19px` (ticket ordinal), `13.5px` (card title, controls), `12.5px` (log line,
label, meta). Nothing is set in capitals.

## Motion

`--ease-enter: cubic-bezier(.2,.7,.3,1)`, used by one animation: the board → ticket
rise. Everything else is a colour transition under the pointer. All of it collapses to
`.01ms` under `prefers-reduced-motion: reduce`.
