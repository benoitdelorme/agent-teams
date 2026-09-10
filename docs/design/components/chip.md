# Chip and badge

Two shapes for two jobs, both fully round (`rounded-full`).

**Chip — an identifier.** Mono at `text-[11px]`, `--color-mute` on `--color-ink-850` inside `--color-ink-700`.
Carries a value you could read aloud or type: `T7`, a Jira key, a count. A Jira chip is
a link and takes `--color-you` ink, because a Jira key is something a person filed.

**Badge — a name.** Sans at `text-[11px]`, no border. Ink is the team's own colour, ground
is that colour at 13%. Carries a team name. Never an identifier, never a count.

**Rules.** A chip never carries a status; a badge never carries a number. Team colours
are generated per name, so a badge's colour is not a token and no other component may
borrow it.
