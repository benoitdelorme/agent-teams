# agent-teams

Run several Claude Code sessions as coordinated teams.

Each team has a lead (Fable 5) that plans and delegates to cheaper workers (Sonnet 5, Opus 5). Teams talk to each other through a strict, low-token protocol. One JSON file configures everything. Runs in [programa](https://github.com/darkroomengineering/programa), one workspace per team.

## How it works

- **gestion** — you talk to it. It plans the feature, dispatches tasks to the other teams and controls the result. It never codes.
- **backend** / **frontend** — each receives tasks, splits them, delegates to its workers, verifies, reports back. They negotiate API contracts directly with each other.

Messages between teams are one line (`DONE T2 | src/api.py:40 — tests green`). Details live in shared files, not in messages.

## Requirements

- Claude Code with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json` → `env`
- programa (or run `bin/teams up --dry-run` and start the printed commands yourself)

## Usage

```bash
git clone git@github.com:benoitdelorme/agent-teams.git teams
cd teams
# edit teams.json: set each team's cwd, title, workers
bin/teams up       # opens one workspace per team, selects gestion
bin/teams down     # stops everything
```

Then describe a feature to gestion and wait.

## The board (kanban web UI)

`teams up` also starts a local web board (URL printed in the terminal, e.g. `board → http://127.0.0.1:52190`) bound live to the ticket files in `shared/tasks/` — dark kanban with five columns: Backlog · TODO · En cours · Ready for QA · Done.

- **Files are the source of truth.** One ticket = one markdown file `shared/tasks/T<n>.md` (frontmatter + `## Description / ## Criteria / ## Log`). The board watches them and updates live over SSE; agents just edit files.
- **Two entry doors, one data path.** Create tickets on the board (backlog → groom → drag to TODO, which wakes gestion with one line typed in its terminal) or talk to gestion, which creates the same files via `teams task new`. Ids (`T<n>`) come from one atomic counter — a Jira key is an optional label on top (`board.jira_base_url` in teams.json makes it a link).
- **Traces for free.** The SendMessage hook mirrors every `TASK/DONE/BLOCKED T<n>` message into the ticket's `## Log` and updates its status (TASK→doing, DONE→qa, BLOCKED→flag). Backlog is never read by gestion.
- Zero dependency: the server is stdlib Python (`bin/teams-board`), the UI one static HTML file. `teams board` starts it alone; `teams down` stops it.

```bash
bin/teams task new "Fix login redirect" --jira LUM-482   # → T7
bin/teams task set T7 status=todo
bin/teams task list --status doing
```

### Existing projects: teach the teams the repo's rules (manual, one-off)

```bash
bin/teams learn all        # per team: scan CLAUDE.md/README/manifests/configs → one cheap Sonnet call → rules/<team>.md (≤60 lines)
bin/teams init <repo>...   # propose a teams.json for one or more repos (one team per detected app), then `learn all`
```

`rules/<team>.md` is cached by a fingerprint of the repo's config files; `teams up` only warns when it is stale — regenerate with `learn <team> --force`. Put your own rules in `rules/<team>.local.md` (never overwritten). The digest goes to the lead's prompt and, trimmed to commands + conventions, to every worker; gestion only sees each team's stack line. The repo's own `CLAUDE.md` is still loaded by Claude Code and wins on conflict.

While it runs:

```bash
bin/teams status       # who is idle/working/dead, PLAN.md tasks, last messages
bin/teams cost         # tokens per team, lead vs workers, per model
bin/teams up --resume  # after a crash: re-attach, restart dead sessions with their context
```

Every message between teams is logged automatically to `shared/LOG.md` (hook-based, costs no tokens).

## Configuration

Everything is in `teams.json`:

- `teams[]` — name, title, cwd, prompt, purpose, `primary: true` for the one you talk to
- `workers` — per team: add, override or remove workers from the catalogue in `agents/`
- `runners` — which command starts a lead (`claude` by default)
- `permission_mode` — `yolo` by default (no prompts)
- `prices_per_mtok` — optional `{ "<model>": { "in", "out", "cache_read", "cache_write" } }` to get $ in `teams cost`

Add a team: `bin/teams add design --cwd ../design`, then edit `prompts/design.md`.

## Files

```
teams.json        config
bin/teams         launcher
prompts/          how leads work, communication protocol, one role file per team
agents/           worker definitions (worker-simple, worker-complex)
rules/            per-team repo digests from `teams learn` (+ your .local.md overrides)
shared/           PLAN.md, CONTRACTS.md and LOG.md, shared by all teams
```

## License

MIT
