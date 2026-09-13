# Changelog

## 0.1.0

First version with the engine / instance split.

- The repository is the engine; `install.sh` symlinks `teams` onto your PATH. A project holds one instance directory (`.teams/` by default) with its own `teams.json`, role prompts, rules, tickets and state. `teams init` scaffolds it. Commands find the instance by walking up from the current directory; a vendored engine at `.teams/engine` takes over automatically.
- `teams init` analyses the project with one cheap model call (tree, manifests, READMEs, proxy and compose configs), proposes the teams with their links and evidence, and asks before writing. `--dry-run`, `--yes`, `--no-ai` (manifest scan only), `--model`.
- `agents/` is now `workers/`. Prompts and worker profiles resolve in layers: instance file first, engine default otherwise.
- The config is found through `--config`, `$TEAMS_CONFIG`, or by walking up from the current directory.
- Terminal drivers in `bin/terminal.py`: `programa` (unchanged behaviour), `tmux` (new), `manual` (commands printed). `terminal` in `teams.json` selects one; `auto` by default. The launcher and the board only hold opaque handles, recorded in `.state/terminal.json` (formerly `surfaces.json`). The protocol fallback is `teams msg <team>` instead of a Programa command, and the roster no longer lists terminal identifiers.
- New config keys: `engine_version`, `language`, `trust_dirs`, `terminal`, `tmux_session`.
- The primary team is called `manager` in the defaults (formerly `gestion`). Existing instances keep whatever name they use.
- Worker descriptions and default prompts are in English; the language used with the human is configurable.
- Board: a ticket is a page at `#T7` instead of a dialog (linkable, back button and `Esc` return to the board), status and blocked flag in its top bar, fields that grow with their content, log lines with a readable time and a colour per speaker, ticket ids linked, empty columns that say what to do, `/` and `n` shortcuts. Ideas taken from PR #4 without its Tailwind and font CDNs: the page stays one dependency-free file.
- Ticket field `jira` and board key `jira_base_url` are now `ref` and `ref_base_url`: any external tracker, not only Jira. Older tickets with `jira:` are still read.
- Protocol: a TASK message carries no criteria in its body any more (they live in the ticket, which the hook already requires); the fallback channel is written as `{{teams}} msg`.
- Demo moved into `examples/demo`: Milestone, a small project tracker (FastAPI + SQLite API, React + Vite + Tailwind web app) rewritten in English with realistic seed data, a `CLAUDE.md` per application and a ready instance.
- Old README became `docs/REFERENCE.md`; the overview README now sits at the root.
