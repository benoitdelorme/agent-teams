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

### Existing projects: teach the teams the repo's rules (manual, one-off)

```bash
bin/teams learn all        # per team: scan CLAUDE.md/README/manifests/configs → one cheap Sonnet call → rules/<team>.md (≤60 lines)
bin/teams init <repo>...   # propose a teams.json for one or more repos (one team per detected app), then `learn all`
```

`rules/<team>.md` is cached by a fingerprint of the repo's config files; `teams up` only warns when it is stale — regenerate with `learn <team> --force`. Put your own rules in `rules/<team>.local.md` (never overwritten). The digest goes to the lead's prompt and, trimmed to commands + conventions, to every worker; gestion only sees each team's stack line. The repo's own `CLAUDE.md` is still loaded by Claude Code and wins on conflict.

While it runs:

```bash
bin/teams status       # who is idle/working/dead, workers per team, PLAN.md tasks, last messages
bin/teams cost         # tokens per team, lead vs workers, per model
bin/teams up --resume  # after a crash: re-attach, restart dead sessions with their context
```

Every message between teams is logged automatically to `shared/LOG.md` (hook-based, costs no tokens).

### Housekeeping (`teams gc`, automatic)

`teams up` starts a detached `teams gc --loop` (every 5 min, zero LLM tokens — no team is ever asked to "clean up"). Each pass:

- removes stale entries from `~/.claude/sessions` (dead pids — they pollute every session's `ListAgents`);
- removes `~/.claude/teams/*` and `~/.claude/tasks/*` of dead sessions (the members list there only ever grows);
- kills a team's `claude` process if its programa workspace was closed by hand;
- detects workers (in-process subagents, tracked via `SubagentStart/Stop` hooks) that produced nothing for `gc.worker_idle_min` and types **one line** into their lead's terminal — the only thing that can stop an in-process agent is its lead's `TaskStop`. Finished workers cost nothing and are not touched; the lead prompt forbids resuming them.

`teams status` shows running/finished workers per team and whether gc is alive. `teams gc --dry-run` prints what a pass would do. `teams down` stops the loop and sweeps once more. Tune in `teams.json` → `gc`.

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
rules/            per-team repo digests from `teams learn` (+ your .local.md overrides) — "how this repo works", ALWAYS injected in the lead and every worker
tools/            on-demand tooling workers Read when their prompt says so, NEVER injected (tools/figma/*.js scripts + gotchas, tools/qa/shoot.mjs)
shared/           PLAN.md, CONTRACTS.md and LOG.md, shared by all teams; shared/design/ = specs, assets, refs produced by the design team
```

Where does a piece of text go? About the repo → `rules/<team>.local.md`. About how ONE worker does its job (tool know-how) → that worker's `agents/<w>.md`. A file a worker opens (script, template, reference) → `tools/`.

## Design team (Figma, token-efficient)

Figma is expensive (tool payloads, 9k-token skills) so it lives in exactly one session: the `design` team. Two sources of Figma tools exist: the claude.ai connector (`mcp__claude_ai_Figma__*`, present in every session of this account) and the `figma` plugin (same tools + 12 skills). The plugin is disabled at user scope (`claude plugin disable figma@claude-plugins-official`); the connector is denied for every team through `defaults.disallowed_tools: ["mcp__claude_ai_Figma__*"]` (→ `--disallowedTools`, tools removed from context) and re-allowed for `design` only (`disallowed_tools_replace: true` + a short deny list of the tools it never needs). The same knob can drop any connector a coding team doesn't need. The design lead never calls Figma itself: disposable workers do, and only compact files come back.

Worker `tools:` restriction is NOT used for design workers: a `tools` list removes `ToolSearch`, and deferred MCP tools then become unreachable (verified). The workers load exactly the Figma tools their prompt names with one `ToolSearch select:` call.

- `design-split` (Fable, vision): page URL → `shared/design/MANIFEST.md` (blocks, components, hashes). One 800 px screenshot.
- `design-autolayout` (Sonnet): absolute-positioned block → auto-layout COPY on Figma page `_autolayout`, via `tools/figma/autolayout.js` (bbox-verified, atomic). Zero images. Human replaces originals in Figma.
- `design-extract` (Sonnet): one node → `blocks/<page>/<block>.md` spec (≤ 60 lines, tokens by name) + `assets/` + `ref/<block>@800.png`. The `get_design_context` payload dies with the worker.
- `design-vision` (Fable, vision): two PNGs → ranked diff list (autolayout faithfulness, or QA of the running app via `tools/qa/shoot.mjs` on `[data-design=<block>]`).

Frontend implements from specs only (never Figma). Messages: `SPEC` / `SPEC-DIFF` (see `prompts/PROTOCOL.md`). `teams status` shows block counts per status from the manifest.

## License

MIT
