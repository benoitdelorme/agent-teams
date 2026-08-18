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
shared/           PLAN.md, CONTRACTS.md and LOG.md, shared by all teams
```

## License

MIT
