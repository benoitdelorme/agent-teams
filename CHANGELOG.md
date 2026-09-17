# Changelog

## Unreleased

- tmux: the terminal you attach in is titled after the primary team (`Driver.title`, a no-op elsewhere), instead of the command that attached it.
- tmux: the session's status bar shows the board URL on the right (`Driver.show`, a no-op for drivers without a status bar); the left side is widened so the session name is not truncated.
- The terminal hosting tmux now shows Claude's state for the teams running inside it. A terminal that draws agent status (Warp's sidebar) learns it from an escape sequence the session writes to its pty; inside tmux that pty belongs to tmux, which swallows it, so every team looked like a plain shell. Each lead's hooks now rebuild that payload and hand it back to Claude Code in its `terminalSequence` output, wrapped in tmux's passthrough envelope: the single tab you attached from carries the Claude icon and the current state. New module `bin/hostterm.py`, one entry per host terminal (`WarpTerminal` today).
- The tmux driver prepares what it creates for that relay: `allow-passthrough all` on every window (a session-level setting never reaches the panes, and `all` is what lets a window nobody is looking at speak), the host terminal's identity copied into the session environment (a tmux server started elsewhere hands its own environment to every pane), one respawn of the first window, which predates those variables, and a `client-attached` hook. Nothing else about tmux changes.
- Passthrough only reaches a client that is already attached, and a lead announces itself at SessionStart, usually long before anyone runs `tmux attach`: the hidden `teams _relay`, run by that hook, replays each live team's state into its own terminal so the host is up to date the moment you look at it.
- Two hook events are now registered per lead, `Notification` and `PermissionRequest`, so a lead waiting for input or for a permission shows as blocked. They carry no team state and change no ticket.
- New terminal driver `warp` for when tmux is not in play: one real Warp tab per team, opened in the active window from a generated `~/.warp/tab_configs/teams-<project>-<team>.toml`, each with its own icon. `auto` picks programa inside Programa, else tmux when installed, else warp inside Warp, else manual.
- Warp cannot be typed into from outside, so such a tab is handed its command when it opens: the hidden `teams _run <team> [--resume-id ID]` records its pid in `.state/runs/<team>.pid` and then execs `claude` in the same process. `up --resume` opens a fresh tab per dead team with its recorded session id; `down` signals the session and hangs up the tab's shell.
- With `warp`, a team's liveness comes from that pid file rather than from the last hook record, so `up --resume` restarts a lead that died in a tab that is still open.
- Driver capabilities instead of driver names: `types_commands` and a `command` argument on `Driver.open`; the existing `attach_hint` carries what `teams up` adds once the teams are started. The launcher and the board branch only on those, and the run recording (`_run` and the pid helpers in `bin/terminal.py`) is reusable by any future terminal that cannot be typed into. `teams msg` refuses a driver that cannot type, and the board reports no delivery channel instead of retrying forever (notifications stay queued).
- `programa` and `manual` are unchanged: same commands, same order, same state files, same output.
- Board: the header brand and tab title now show the project name (new `project` config key, defaulting to the project directory name), so several boards from different projects are distinguishable.

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
