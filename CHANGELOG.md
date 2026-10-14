# Changelog

## 0.2.0

Remote instances: the teams run on another machine, you watch and drive them from this one.

- `teams link <host>:<path>` points a local directory at an instance living on another machine: it checks over ssh that the instance answers, then writes `.teams/remote.json`. Commands typed anywhere under that directory act over there. `--remote <host>:<path>` and `$TEAMS_REMOTE` name a target without a file.
- `teams up` starts the teams on the server, in tmux, then opens one local view per team through your own terminal driver: a Programa workspace, a tmux window, or a printed command. `teams attach` opens the missing views again without touching the teams. `teams down` stops the teams over there, then closes the views. Closing a view never stops a team.
- A view reconnects by itself when the connection drops or this machine wakes up; a detach or stopped teams end it. The board is forwarded to the same port on `127.0.0.1` here, with the same reconnection.
- Every other command (`status`, `task`, `msg`, `cost`, `learn`, `board`, `cmd`, `add`, `up --dry-run`) is relayed over ssh as it is, through the remote user's login shell. Every word sent to a shell, over there or here, is put between single quotes, so it arrives as typed whatever the shell: zsh, for one, expands a bare word starting with `=`.
- `teams status --json` prints one line describing the running instance for programs: driver, terminal handles, liveness, board address, engine version.
- New files: `bin/remote.py` in the engine; `remote.json` and `.state/views.json` in an instance directory. `remote.json` belongs to one machine, and the instance `.gitignore` written by `init` now ignores it.
- Upgrading from 0.1.0: nothing changes for an instance without a `remote.json`. Add the line `remote.json` to an existing instance's `.gitignore` by hand. `teams up` reports that the instance was created for engine 0.1.0 until you set `engine_version` to `0.2.0` in its `teams.json`. A server must run this version too: an older engine there does not know `status --json`, and `teams link` says so.

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
