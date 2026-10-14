# Reference

Commands, configuration, files and recovery behaviour of the engine. The [README](../README.md) gives the overview and the getting-started path; the [protocol](../prompts/PROTOCOL.md) defines the messages leads exchange.

## Vocabulary

- **Engine**: this repository. Launcher, board, protocol, default prompts and worker profiles. Cloned once, linked onto your PATH with `install.sh`.
- **Instance**: one directory per project, `.teams/` by default, created by `teams init`. Holds the project's `teams.json`, its role prompts, generated rules, tickets and runtime state.
- **Team**: one Claude Code session (the lead) in its own terminal, with a working directory and a role prompt. The team marked `primary` is the manager you talk to.
- **Terminal driver**: how terminals are opened and typed into: `programa`, `tmux` or `manual`. See [Terminals](#terminals).
- **Worker**: a native Claude Code sub-agent a lead launches for one bounded assignment. Profiles live in `workers/`.
- **Ticket**: one markdown file `shared/tasks/T<n>.md`, the single source of truth for a task.

Paths below are relative to the instance unless stated otherwise.

## How the instance is found

Every command runs as `teams <command>` from anywhere inside the project. The instance is resolved in this order:

1. `teams --remote <host>:<path> <command>`: the instance of that project on another machine (see [Remote instances](#remote-instances)). Refused together with `--config`, and when abbreviated: write `--remote` in full.
2. `teams --config <file> <command>` (both options go before the command)
3. `$TEAMS_CONFIG`
4. `$TEAMS_REMOTE`, a `<host>:<path>` target
5. walking up from the current directory. At each level, `.teams/remote.json` or `teams/remote.json` makes the instance remote; otherwise `.teams/teams.json`, then `teams/teams.json`, then `teams.json` makes it local. The nearest level holding one of them decides, and a `remote.json` beside a `teams.json` wins.

`teams init` is sent to another machine by `--remote` only, never by `$TEAMS_REMOTE` or by a `remote.json` found above; `teams link` always runs here.

Claude sessions started by `teams up` receive `TEAMS_CONFIG` and `TEAMS_TEAM` in their environment, so the agents run the same commands without any flag, and never leave the machine they run on.

If the instance contains `engine/bin/teams` (a vendored engine, typically a git submodule), the global `teams` command hands over to it. This pins an engine version for one project without changing anything else.

## Commands

| Command | What it does |
| --- | --- |
| `teams init [--dir .teams] [--model m] [--no-ai] [-y] [--dry-run] [--language L] [--force] [repo...]` | Create an instance. The project root is the parent of `--dir`. A snapshot of it (or of the given repositories) goes to one model call (`--model`, Sonnet 5 by default, no tools, no session): tree three levels deep, manifests, READMEs, `CLAUDE.md`, compose and dev-server configs, capped at about 12k tokens. The answer is a proposal of one to six teams with directory, purpose, stack, verification commands, interfaces and evidence, validated (directories must exist inside the project, names must be unique) and shown to you; `--dry-run` stops there, `--yes` accepts without asking, a non-terminal without `--yes` refuses. `--no-ai`, or a failed call, falls back to detecting frontend and backend manifests two levels deep (a single `dev` team when nothing is recognised). Writes `teams.json`, the template files and one role prompt per team: the engine's role for its kind with a `## This project` section, or the filled template for other kinds. Only `.teams/` and `teams/` are discovered automatically; another `--dir` needs `TEAMS_CONFIG`. |
| `teams up [--dry-run] [--resume]` | One terminal per team through the selected driver, Claude started in each, board started, manager selected. `--dry-run` prints the commands and writes the generated prompts without starting anything. `--resume` re-attaches to a running setup, recreates missing terminals and restarts dead sessions with their recorded session id. With the `manual` driver: prints the commands to run yourself and starts the board detached. |
| `teams down` | `/exit` every team, close their terminals, stop the board. |
| `teams status [--json]` | Liveness per team, ticket summary, tail of `shared/LOG.md`. `--json` prints one line instead, for programs: whether the teams are up, the driver, the start time, the engine version, each team's terminal handle and status, the board address. |
| `teams cost` | Token usage of the current run per team, lead versus workers, per model. Dollars when `prices_per_mtok` is set. |
| `teams task new "<title>" [--team t] [--status s] [--ref PROJ-123] [--desc ...] [--criteria ...] [--scope ...] [--verify ...] [--decisions ...] [--depends ...]` | Create a ticket. Prints its id. Default status `backlog`. |
| `teams task set T7 key=value ...` | Change `title`, `team`, `status`, `blocked`, `ref`, `description`, `criteria`, `scope`, `verify`, `decisions`, `depends`. Status transitions are validated. |
| `teams task log T7 "<note>"` | Append one line to the ticket's `## Log`. |
| `teams task list [--status s]` / `teams task show T7` | Read tickets. |
| `teams learn [team\|all] [--force] [--dry-run] [--model m]` | Summarize a team's repository (CLAUDE.md, README, manifests, configs) into `rules/<team>.md` through one cheap model call (five-minute timeout). `all` covers every execution team, not the manager. Cached by a fingerprint of those files. |
| `teams add <name> --cwd <dir> [--purpose "..."]` | Register a team in `teams.json` (`--cwd` relative to your shell, stored relative to the instance) and create `prompts/<name>.md` from the template. |
| `teams board [--port N]` | Start the board alone. |
| `teams msg <team> <text...>` | Type text into a team's terminal through the driver. Fallback channel; it does not run the message hooks. |
| `teams cmd <team>` | Print the exact `claude` command generated for a team. |
| `teams link <host>:<path> [--dir .teams]` | Point the current directory at an instance on another machine: check over ssh that it answers, then write `<dir>/remote.json` and print the teams found there. An existing target is replaced and named. See [Remote instances](#remote-instances). |
| `teams attach` | Remote instances only: open the local views that are missing, forward the board, select the manager's view. The teams are not touched. |

`--remote <host>:<path>`, before the command, runs it on another machine without a `remote.json`.

## Configuration: `teams.json`

Paths are relative to the file. Any `prompts/` or `workers/` file present in the instance overrides the engine file of the same name.

### Top level

| Key | Default | Meaning |
| --- | --- | --- |
| `engine_version` | written by `init` | `teams up` warns when the engine checkout reports another version (`VERSION` file). Other commands stay silent so agents never see the warning. |
| `language` | `English` | Language the leads use with the human. Inter-team messages stay in English. |
| `shared_dir` | `shared` | Directory holding tickets, log, roster and optional PLAN.md / CONTRACTS.md. |
| `permission_mode` | written as `yolo` by `init` | `yolo` (no prompts, `--dangerously-skip-permissions`), `acceptEdits`, `default` or `plan`. Absent: Claude's own default, which prompts. Overridable per team. |
| `trust_dirs` | `true` | `up` marks every team directory as trusted in `~/.claude.json` so no dialog blocks a terminal. |
| `terminal` | `auto` | `programa`, `tmux`, `manual`, or `auto`: programa when running inside it, else tmux when installed, else manual. |
| `tmux_session` | `teams-<project dir>` | Name of the tmux session holding this instance's windows. |
| `board` | `{"port": 0, "ref_base_url": ""}` | Port `0` lets the OS pick. `ref_base_url` is prefixed to a ticket's `ref` to make it a link on the board (`https://xxx.atlassian.net/browse/`, `https://github.com/org/repo/issues/`…). |
| `shell_prompt_regex` | `(➜\|→\|❯\|\$\|%\|#) ` | Pattern of the shell prompt the launcher waits for before typing into a new terminal. |
| `session_prefix` | empty | Prefix Claude adds to session names, used to match message recipients to team names. |
| `prices_per_mtok` | none | `{ "<model>": { "in", "out", "cache_read", "cache_write" } }` in dollars per million tokens, for `teams cost`. |
| `defaults` | see below | Values inherited by every team. |
| `runners` | `{"claude": {"command": "claude"}}` | Named ways to start a lead. |
| `teams` | | The list of teams. |

### `defaults`

| Key | Meaning |
| --- | --- |
| `model` | Lead model. `claude-fable-5-1` by default. |
| `runner` | Runner name for leads. |
| `add_dirs` | Extra directories every lead may access. |
| `workers` | The worker catalogue: `"<name>": { model, description?, vars?, file? }`, or `"<name>": "<model>"` as a shortcut. `<name>` is the file `workers/<name>.md`. |

### One team

| Key | Meaning |
| --- | --- |
| `name` | Identity used by the other agents. Lowercase letters, digits, hyphens. Unique. |
| `title` | Terminal name (Programa workspace, tmux window). |
| `cwd` | Working directory. Must exist. |
| `prompt` | Role file under `prompts/`. Defaults to `<name>.md`. |
| `purpose` | One line shown to every lead in the roster. |
| `primary` | `true` for the one team you talk to. Exactly one. |
| `enabled` | `false` keeps the configuration without launching the team. |
| `model`, `runner`, `permission_mode`, `add_dirs` | Per-team overrides of the defaults. |
| `workers` | Merged with `defaults.workers`: add a profile, override `model` or `description`, or set a name to `false` to remove it. |
| `workers_replace` | `true` ignores `defaults.workers` entirely. |

Worker prompts can use `{{team}}`, `{{cwd}}`, `{{shared_dir}}`, `{{language}}`, `{{rules}}` and any `vars` defined for that worker. Role prompts, `_common.md` and `PROTOCOL.md` get `{{team}}`, `{{cwd}}`, `{{shared_dir}}`, `{{language}}`, `{{root}}` (the instance), `{{engine}}` and `{{teams}}` (how to invoke the CLI); the rules are appended as a section, not as a variable.

### One runner

| Key | Meaning |
| --- | --- |
| `command` | Binary that starts the lead. |
| `brain` | Informational: the model that actually runs when the binary ignores `--model`. Shown in the roster. |
| `drop_flags` | Flags to strip from the generated command for runners that set their own model. |
| `healthcheck`, `start` | URL to probe before `up`, and the shell command that starts the service when it does not answer. |

## What a lead receives

The generated system prompt (kept in `.state/prompt-<team>.md`) concatenates, in order: `prompts/_common.md`, the list of workers with their models and descriptions, the team's role prompt, the repository rules (`rules/<team>.md` digest, then `rules/<team>.local.md`), the roster of all teams (name, model, purpose, directory), and `prompts/PROTOCOL.md`. Workers are passed with `--agents` from `.state/workers-<team>.json`; each worker gets the rules digest trimmed to commands, conventions and prohibitions.

Hooks are attached through `--settings`: session start and end, prompt submit, stop, and the three `SendMessage` tool events. They record liveness in `.state/sessions/<team>.json` and mirror recognized messages into tickets.

## Tickets

One file per ticket, allocated from an atomic counter (`shared/tasks/.counter`):

```markdown
---
id: T7
title: Archive a project
team: backend           # or "-" until assigned
status: doing           # backlog | todo | doing | qa | done
blocked: false          # a flag, not a status
ref: PROJ-123           # optional external reference (Jira key, issue number…)
created: 2026-09-13T10:12:00
updated: 2026-09-13T10:40:12
by: manager             # human | <primary team>
---

## Description
## Criteria
## Scope        (optional)
## Verify       (optional)
## Decisions    (optional)
## Depends      (optional)
## Log
```

Permitted transitions: `backlog → todo`, `todo → backlog | doing`, `doing → todo | qa`, `qa → doing | done`, `done → todo`. Only the human and the primary team may change frontmatter; the team a ticket is assigned to may append to its `## Log`. Every write takes one shared lock across the read-modify-write and replaces the file atomically. The CLI, the board and the hooks share that code.

Hooks mirror recognized messages after the send succeeds: `TASK T7` sets `doing` and the team, `DONE T7` sets `qa`, `BLOCKED T7` sets the flag, and each header lands in the ticket's `## Log` and in `shared/LOG.md`. A message referring to an unknown ticket or sent by the wrong team is rejected before sending. Session and tool-use ids deduplicate replayed events; when they are missing, the message is sent but the ticket is left unchanged and the lead gets a warning.

`.state/messages/` records `attempted`, `sent`, `failed` and `sync_failed` events for the current run. `sent` means the tool succeeded, not that the recipient processed the message. Inspect `sync_failed` records before reconciling a ticket by hand; do not resend the original task blindly.

## Terminals

`bin/terminal.py` holds the drivers. Each offers the same few operations (open a terminal, wait for its shell, type text, check it exists, find its tty, select it, close it) and the launcher only ever holds an opaque *handle* per team, recorded with the driver name in `.state/terminal.json`.

| Driver | Terminal per team | Board server | Notes |
| --- | --- | --- | --- |
| `programa` | a named workspace | a tab in the manager's pane | Required inside Programa: `programa send` only reaches clients living in a real pane, so a detached board could never wake the manager. |
| `tmux` | a window of the session `teams-<project>` (`tmux_session` to rename) | a window of the same session | The session is detached; `teams up` prints the attach command when you are not already inside tmux. |
| `manual` | none: commands are printed | detached process | A run is still recorded (so `status`, `down` and the `up` guard work), but the board cannot wake the manager and `teams msg` has nowhere to type. |

`auto` picks programa inside Programa, else tmux when installed, else manual. Later commands (`status`, `msg`, `down`, `board`) use the driver recorded by `up`, so switching multiplexers between `up` and `down` is not supported. `teams up --dry-run` prints the commands with any driver and records nothing.

## The board

`teams up` starts a local kanban bound live to the ticket files. Five columns: Backlog, TODO, In progress, Ready for QA, Done. Blocked is a red mark on the card. The server is stdlib Python (`bin/teams-board`), the UI one static HTML file; it watches file mtimes twice a second and pushes changes over SSE.

- Creating, editing, assigning, commenting and deleting tickets on the board writes the same files the CLI writes.
- A ticket opens as a page at `#T7`: the address is shareable, the browser back button returns to the board, `Esc` too. Status and the blocked flag sit in its top bar; description, criteria and the optional work context grow with their content; the log shows the time of each line and colours who is speaking (agents at work in blue, finished in green, blocked in red, you in amber), and links every ticket id it mentions.
- Keyboard: `/` focuses the filter, `n` starts a new ticket in Backlog, `Esc` leaves a field, closes the ticket or clears the filter.
- Moving a ticket to TODO, or commenting with the notify option, queues a notification for the manager in `.state/notifications.json`. Delivery types one line into the manager's terminal. The queue is retried every five seconds, survives restarts, merges identical pending items and preserves order. The header shows the pending count; hovering it tells whether a delivery channel is available.
- The board server runs where the driver puts it (see above). With the `manual` driver the board works but cannot wake the manager.
- A notification delivered right before a crash can be delivered twice; the manager checks the ticket before dispatching.

## Remote instances

An instance can live on another machine. The teams, the repository, the hooks and the board then run there, in tmux, and this machine relays commands over ssh and shows one view per team. The sessions survive this machine sleeping, rebooting or losing the network. Nothing changes for an instance without a target.

**The target** is a `<host>:<path>`: anything `ssh` accepts as a destination (an alias from `~/.ssh/config`, `user@host`) and the project directory over there (a leading `~` is expanded by the server). `teams link <host>:<path>` records it in `.teams/remote.json` of the current directory, which can be a clone of the project or a folder kept only for this; `--remote` and `$TEAMS_REMOTE` give one without a file. Several directories can point at several servers and projects, each with its own views.

`remote.json` belongs to one machine and stays out of git. The `.gitignore` written by `init` ignores it; in an instance created before 0.2.0, add the line `remote.json` by hand.

| Key | Default | Meaning |
| --- | --- | --- |
| `host` | required | The ssh destination. |
| `path` | required | The project directory on the server, from which `teams` finds the instance. |
| `command` | `teams` | The command run over there when `teams` is not on the login shell's PATH, for instance `~/agent-teams/bin/teams`. It is written into the remote shell line as it is. |
| `ssh_options` | `[]` | Extra `ssh` arguments, as a list: `["-p", "2222"]`. |
| `terminal` | `auto` | The driver of the local views, as in `teams.json`: `programa`, `tmux`, `manual` or `auto`. `tmux_session` and `shell_prompt_regex` are read here too. |
| `mouse` | `true` | `false` leaves tmux's mouse mode off in the views. |

**Prerequisites.** On the server: tmux; this engine, 0.2.0 or later, with `teams` on the PATH of the user's login shell (or `command`); an authenticated Claude Code with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`; an instance created there with `teams init` and running with the `tmux` driver, which `auto` picks on a machine without Programa. Here: this engine, and ssh access that asks for nothing, a key or an agent, because the status call and the board forward run without a terminal. Both engines should be the same version: a difference is reported on stderr, and an engine that does not know `status --json` is refused with the advice to update it. The remote mode has been run from a Mac with Programa against an Ubuntu 22.04 server with tmux 3.2a and bash as the login shell.

**How a command gets there.** `teams <arguments>` becomes `ssh <host>` running `exec "$SHELL" -lc 'cd <path> && teams <arguments>'`: the remote user's login shell, so its PATH finds `teams` and `claude`. Every word is put between single quotes, the path (but a leading `~`, left for the server to expand) and each argument, so no shell over there expands it: a word such as `=ls`, which zsh would turn into `/bin/ls`, arrives as typed. `--remote` is removed, and a terminal is requested only when your stdin and stdout are both terminals, so `teams task list | grep doing` stays clean. The exit code is the remote one. The suites run this line, and the view line below, under sh, bash, zsh, dash and ksh as the server's shell, those installed on the machine that runs them; fish is not tested.

**`teams up`** asks the server for its status, refuses when the teams are already up there (`teams attach` is then the command), runs `teams up` over there, then opens the views. `teams up --resume` resumes over there, then opens the missing views. `teams up --dry-run` is only relayed.

**`teams attach`** opens what is missing and leaves the rest alone. For each team, the manager last: when it has no view yet or its terminal is gone, a new terminal is opened; when the terminal is still there but nothing in it is connected any more, the view command is typed into it again; when the view is running, nothing happens. A team that has no terminal on the server is reported and skipped. With the `manual` driver the commands are printed for you to run. When the server reports another run than the one the views were opened for, the old views and the old board forward are closed first. Finally the manager's view is selected.

**`teams down`** stops the teams over there first, then closes the views, stops the board forward and forgets them.

**A view** is a terminal of the local driver, titled like its team, into which a `sh -c` loop is typed. The loop runs `ssh -t <host>` and, over there, through the login shell as above, `tmux new-session -A -s <session>-<team> -t =<session>`, then selects the team's window: the view uses the tmux the teams were started with. `<session>-<team>` is a tmux session *grouped* with the teams' one: every view sees the same windows and keeps its own current window, so two views show two teams at once. Every word of that line is single-quoted at each shell it crosses, which makes it long in a process list. The loop runs ssh again, 3 seconds later, each time it exits with 255, ssh's own code for a connection that failed or was lost. Any other exit, such as a detach (`C-b d`) or stopped teams, ends the loop and gives the terminal back to its shell. A connection that hangs rather than fails is declared dead after about 45 seconds (`ServerAliveInterval=15`, `ServerAliveCountMax=3`). When the server has no terminfo entry for your `TERM`, the view uses `xterm-256color`. Mouse mode is switched on for the view sessions only, so the wheel scrolls the session's history.

**The board** stays bound to the server's `127.0.0.1`. A background loop of the same kind runs `ssh -N -L <port>:127.0.0.1:<port> <host>`, so the address printed by `teams up` works here as it is. When that port is already used on this machine, nothing is started and the command to run by hand with another local port is printed, its words quoted, ready to paste into any shell. The loop's output goes to `.state/tunnel.log`.

**What this machine remembers** is in `.state/views.json` beside `remote.json`: the driver, one terminal handle per team, the run they belong to and the board forward's process. For a target given by `--remote` or `$TEAMS_REMOTE` it is under `~/.local/state/teams/<host-and-path>/` instead.

**Limits.**

- A view follows its tmux group: when its team's window is destroyed and recreated (`teams up --resume` after a dead session), the view shows another team's window. Close that view and run `teams attach`.
- `teams attach` types into a view's terminal when it finds no view running there. Do not use a view's terminal for anything else.
- The state of the teams (working, waiting for you) is not shown on the views; `teams status` and the board have it.
- fish is not tested, neither as the server's login shell nor as your terminal's shell: its single quotes give `\'` and `\\` a meaning.
- The local side needs a POSIX system; Windows is not supported.

## Runs, resume and archives

A fresh `teams up` starts a new run: previous `.state/sessions/` and `.state/messages/` move to `.state/history/<timestamp>/`, and `teams cost` reads the current run only. `up --resume` keeps the run, recreates missing terminals, reuses live sessions and restarts dead ones with their recorded session id; a team without one starts fresh. `teams down` closes the terminals and clears `.state/terminal.json`; tickets, rules and the notification queue are untouched.

## Repository rules

`teams learn` sends the team's `CLAUDE.md`, README, manifests and tool configs to one cheap model call and writes a digest of about sixty lines to `rules/<team>.md`: stack, commands, structure, conventions, prohibitions, files worth reading. It is cached by a fingerprint of those files; `up` only warns when the digest is stale. Your own notes go in `rules/<team>.local.md`, never overwritten. The lead gets the full digest, workers get commands and conventions, the manager gets each team's stack line. The repository's own `CLAUDE.md` is still loaded by Claude Code and wins on conflict.

## Files

Engine (this repository):

```
bin/teams          launcher and CLI
bin/teams-board    board server
bin/terminal.py    terminal drivers (programa, tmux, manual)
bin/remote.py      remote instances: target, relay over ssh, local views, board forward
bin/tasklib.py     ticket model, validation, locked atomic writes
bin/hooklib.py     session tracking and message mirroring (called by the Claude hooks)
bin/storage.py     locked JSON helpers
prompts/           _common.md, PROTOCOL.md, _template.md, default roles (manager, backend, frontend)
workers/           default worker profiles (worker-simple, worker-complex)
template/          files copied into a new instance
tools/board/       the board UI
examples/demo/     two sample apps and a ready instance
docs/              this reference, the board design note, illustrations
tests/             python unittest suites and a node test for the board UI
install.sh         symlinks bin/teams into a directory on your PATH
VERSION            engine version, recorded in each instance
```

Instance (one per project):

```
.teams/teams.json  configuration
.teams/remote.json a target on another machine, written by `teams link`: with it, commands act over there
.teams/prompts/    this project's role prompts (override engine files of the same name)
.teams/workers/    optional worker overrides
.teams/rules/      generated digests and your .local.md notes
.teams/shared/     tasks/, LOG.md, .roster.json, optional PLAN.md and CONTRACTS.md
.teams/engine/     optional vendored engine to pin a version
.teams/.state/     generated prompts, sessions, messages, notifications, terminal handles, board state (gitignored)
.teams/.state/views.json   for a remote instance: its local views and its board forward
```

The instance `.gitignore` written by `init` ignores runtime state, `remote.json` and, by default, the tickets; remove two lines to version them.

## Tests

```bash
python3 -B -m unittest discover -s tests -v
node --test tests/board-ui.test.cjs
```

The suites cover concurrent ticket updates, message routing and replay, session lifecycle, the terminal drivers, remote instances (target resolution, the relay, the views and the board forward; the relay line and the view line are read by real shells, sh, bash, zsh, dash and ksh, each reported as skipped where it is not installed, through a fake ssh and tmux), board notifications, a real loopback HTTP server with temporary data, and the permitted UI transitions. Model calls, ssh and terminal commands are mocked.
