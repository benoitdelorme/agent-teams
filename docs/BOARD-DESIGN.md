# Task Board — design note

A local web kanban bound live to what the agents are doing. Started by `teams up`, it is
the second entry door for tickets (the other one being the manager's terminal).
Status: historical design document. The board is implemented (`bin/teams-board`,
`tools/board/index.html`); the [README](../README.md) and [REFERENCE](REFERENCE.md)
describe the current behavior. Programa-specific mechanics mentioned below now sit behind
the terminal drivers of `bin/terminal.py` (tmux works the same way).

## 1. Guiding principle: files remain the source of truth

No database, no server state. The truth lives in markdown files the agents already know
how to read and write. The web server is only a **view plus a pen** on those files:

- **agents → UI**: an agent edits a ticket file → the server detects the change (watch)
  → pushes an SSE event → the UI updates.
- **UI → agents**: the human creates or moves a ticket → the server writes the file →
  and *wakes* the manager through `programa send` (the `teams msg` mechanism) only when
  it matters (a move to TODO).

Consistent with the repository's philosophy: `bin/teams` is pure stdlib Python; so is the
board server.

## 2. Data model: one file per ticket

`shared/PLAN.md` (a single table) is bad for concurrent editing: the manager and the UI
would write the same table. We move to **one file per ticket**:

```
shared/tasks/
  T1.md
  T2.md
  ...
  .counter          # next id (server and manager increment it atomically)
```

Ticket format (`shared/tasks/T3.md`):

```markdown
---
id: T3                    # internal number, ALWAYS present (see §2.1)
title: Auth layer frontend
team: frontend            # or "-" until assigned
status: doing             # backlog | todo | doing | qa | done
blocked: false            # red badge, not a column
ref: PROJ-123             # external reference, OPTIONAL (Jira key, issue number…)
created: 2026-08-31T15:20
updated: 2026-08-31T16:02
by: human                 # human | manager
---

## Description
Context / goal, written by the human (UI) or the manager.

## Criteria
- `pnpm build` + `pnpm lint` green
- wrong creds shows error

## Log
- 16:02 manager → frontend | TASK T3 | auth layer, see criteria
- 16:41 frontend → manager | DONE T3 | lib/auth.tsx, pages/Login.tsx — build green
- 16:45 manager: spot-check ok, moved to qa
```

### 2.1 Mandatory internal number, optional external reference

Every ticket has **an internal number `T<n>` no matter what**, allocated at creation from
`shared/tasks/.counter` (atomic increment: read + write under `os.rename`, whether the
creator is the web server or the manager). It is the authority everywhere:

- **`id` = canonical identity**: file name (`T<n>.md`), protocol `<ref>` (TASK T3,
  DONE T3…), `## Log` key, hook target. Never reused, never renumbered, independent of
  any external tool.
- **`ref` = a plain label** (optional): set at creation or later in the dialog. The
  system never uses it: agents and hooks only reason about `T<n>`. The UI shows it on
  the card next to the internal number (`T3 · PROJ-123`) and turns it into a link when
  `teams.json` defines `board.ref_base_url` (`https://xxx.atlassian.net/browse/`).
  Search and filter work on either.
- Extensible without migration: when GitHub or Linear is needed, add a key
  (`github: #142`) with the same label status; the internal `id` stays the pivot.

A task born in the terminal (manager) and a task born in the UI draw from the same
counter: no collision, one sequence.

- The kanban = the `status` field of the frontmatter. Moving a card = rewriting one line.
- **The trace lives in `## Log`**: fed automatically (see §5) and manually by the agents
  ("detail lives in files" is already the protocol).
- Writes are always atomic (tmp + `os.rename`) on both sides.
- `shared/PLAN.md` keeps the "Goal / Contracts" role of the current feature, but the task
  table disappears in favor of `shared/tasks/`. `plan_summary()` in `teams status` reads
  the directory.

### Statuses and semantics

| status  | who sets it                    | meaning |
|---------|--------------------------------|---------|
| backlog | human (UI) or manager          | ideas / not ready. **Invisible to the manager** (prompt rule + the server never notifies on it) |
| todo    | human (drag) or manager        | ready to dispatch → the manager is woken |
| doing   | manager at dispatch            | TASK sent to a team |
| qa      | manager on DONE                | to verify (worker spot-check / human) |
| done    | manager after verification     | finished |

`blocked: true` is a cross-cutting flag (card marked red in its column), set when a
BLOCKED arrives. Not a sixth column.

## 3. The server: `teams board` (stdlib Python, zero dependency)

One file `bin/teams-board` (~400 lines), or a `bin/teams` command:

- **HTTP**: `http.server.ThreadingHTTPServer`, bound to `127.0.0.1:0` → the OS picks a
  free port (nothing to scan). Port + pid written to `.state/board.json`.
- **API** (JSON, minimal):
  - `GET /api/tasks` — all tickets (frontmatter + rendered body)
  - `POST /api/tasks` — create (backlog by default)
  - `PATCH /api/tasks/T3` — status / title / team / blocked
  - `POST /api/tasks/T3/comment` — the human appends a line to `## Log`
  - `GET /api/state` — roster + liveness (re-reads `.state/sessions/*.json`)
  - `GET /events` — **SSE** (one stream: `task-changed`, `state-changed`)
- **Watch**: poll mtimes of `shared/tasks/` + `.state/sessions/` every 500 ms (one
  `os.scandir` over ~50 files, negligible, reliable on macOS; no need for FSEvents).
  Diff → SSE event with the full ticket (the UI patches, no re-fetch).
- **Waking the manager**: when a ticket **enters `todo` from the UI**, the server runs the
  equivalent of `teams msg manager`:
  `programa send --workspace … --surface … "NEW T7 | <title> — read shared/tasks/T7.md, plan and dispatch\n"`.
  This is the only push toward an agent. Everything else (doing/qa/done set by the
  manager, logs) reaches the UI through the watch. A human comment on a ticket in
  progress can optionally notify the manager (`COMMENT T7 | see Log`), behind a toggle.

### Lifecycle

- `teams up`: starts the server **in a "board" tab of the manager's pane** (through
  `programa new-surface --pane`) and prints `board → http://127.0.0.1:xxxxx` in the
  terminal that ran `up`. Constraint discovered while implementing: `programa send`
  refuses orphan clients (outside the tree of a live pane), so a detached server could
  never wake the manager. The tab solves that without adding a workspace and keeps the
  server logs visible. Outside programa: detached subprocess (no wake, the board stays
  usable for reading and writing).
- `teams down`: kills the pid in `.state/board.json`.
- `teams board`: start or restart on its own (useful outside programa); `teams up --resume`
  restarts it if dead.
- Dead server ≠ broken system: the agents keep going, the UI catches up on restart
  (everything is in the files).

## 4. Two entry doors, one data path

1. **Web**: create in backlog → refine → drag to TODO → the server writes the file and
   wakes the manager → the manager reads `shared/tasks/T7.md`, assigns `team`, moves to
   `doing`, dispatches `TASK T7 | …`.
2. **Terminal**: the human talks to the manager as before → the manager **creates the
   ticket files itself** (its prompt replaces "write the PLAN.md table" with "one file per
   task in `shared/tasks/`, statuses backlog|todo|doing|qa|done") → the UI sees them
   appear live through the watch.

Neither path talks to the other directly: both write the same files, the watch makes
everyone converge. No double truth possible.

## 5. Automatic traces: extend the existing hook

The `PreToolUse/SendMessage` hook of `bin/teams` already logs every inter-team message to
`LOG.md`. Extension: when the message header matches `^\w+ (T\d+)` (TASK T3, DONE T3,
BLOCKED T3…), the same line is **also appended to the ticket's `## Log`**. Effects:

- every ticket carries the full history of its exchanges **without changing the prompts**;
- `BLOCKED T3` sets `blocked: true` on the way; `DONE T3` can set `status: qa`
  automatically (the manager confirms afterwards). Two hook rules, zero tokens spent.

Agents remain free to write richer notes in the ticket body (result, changed paths); the
protocol already pushes them to.

## 6. The UI: one page, dark, no framework

**Recommendation: no shadcn.** shadcn = React + Tailwind + node_modules + build, for five
columns and a dialog. The repository is zero-dependency and the need is small; a single
`board.html` (~600 lines of vanilla HTML/CSS/JS, served by the server) gives the same
high-end rendering, loads in under 50 ms and introduces no build chain. (Option B if the
UI has to grow: Vite + React + shadcn, `dist/` committed, served statically; same server,
same API; the API/SSE boundary makes the swap painless.)

- **Theme**: dark only. Background `#0e1013`, cards `#16191d`, borders `#23272d`, text
  `#e6e8ea`, per-team accents (frontend cyan, backend violet, manager amber), `blocked`
  red. Font `Inter, -apple-system, system-ui, sans-serif` (no serif), 13–15 px sizes,
  Linear-like density.
- **Layout**: five columns (Backlog · TODO · In progress · Ready for QA · Done) in CSS
  grid, vertical scroll per column, counter per column. Header: feature name (PLAN.md),
  team liveness dots (green = working, grey = idle, red = dead, from `/api/state`), SSE
  connection dot.
- **Card**: `T7` + team badge + title + last-activity timestamp + blocked icon.
- **Drag & drop**: hand-written pointer events (~80 lines, no library). Optimistic: the
  card moves immediately, `PATCH` behind, rollback on error. The SSE echo of its own
  write is deduplicated by `updated`.
- **Ticket dialog**: editable frontmatter (title, team, blocked), description/criteria,
  and the `## Log` rendered as a chat-like stream that **grows live** while the agents
  work. Human comment area at the bottom.
- **Creation**: `+` button in Backlog, inline input (title, Enter = created; the server
  allocates `T<n>` and returns it), details and optional reference field in the dialog.
- **Live**: `EventSource` with automatic reconnection; on reconnect a `GET /api/tasks`
  resynchronizes. No websocket: SSE is enough (one-way server→UI stream, writes go
  through the API).

## 7. What changes in the existing code (small)

| file | change |
|---|---|
| `bin/teams` | `cmd_up`/`cmd_down`/`resume`: start/stop the board, print the URL; hook: append to the ticket's `## Log` + blocked/qa rules; `plan_summary()` reads `shared/tasks/` |
| `bin/teams-board` | **new**: HTTP + SSE + watch server (stdlib) |
| `board.html` (in bin/ or tools/board/) | **new**: the UI |
| `prompts/manager.md` | ticket files instead of the PLAN.md table; allocate `T<n>` through `.counter`; "ignore status: backlog"; set doing/qa/done |
| `prompts/PROTOCOL.md` | `<ref>` points to `shared/tasks/T<n>.md`; one line about statuses |
| `.gitignore` | `shared/tasks/` (runtime content, like LOG.md) |
| `teams.json` | optional: `board: {"port": 0, "open": false, "ref_base_url": "https://…/browse/"}` |

## 8. Cost, performance, risks

- **Token cost**: nearly zero. The board never talks to an LLM; the only interaction is
  one `NEW T7 | …` line typed into the manager's terminal, the same cost as a human
  message. Automatic traces go through the hook (free).
- **Performance**: mtime polling twice a second on a local directory, SSE with one client
  (or two or three tabs), files under 10 KB. Nothing to optimize.
- **Risks and answers**:
  - *Concurrent write on the same ticket* (the manager edits during a drag): rare
    (one file per ticket), atomic writes, last write wins on the frontmatter, `## Log` is
    append-only. Acceptable for a single-user tool.
  - *The manager misses the wake-up* (busy session): `programa send` types into the
    terminal, the message is handled on the next turn, the same guarantee as `teams msg`.
  - *Frontmatter broken by an agent*: the server validates at parse time; an unreadable
    ticket shows as a "⚠ needs repair" card instead of a crash.

## 9. Proposed implementation order

1. Ticket model: `shared/tasks/`, parser/writer in `bin/teams`, `plan_summary` migration,
   manager prompt. (The system already works better, without any UI.)
2. Server: API + watch + SSE + start/stop in `up`/`down`.
3. UI: columns + cards + drag + dialog + live.
4. Wake loop (`todo` → programa send) + automatic traces in the hook.
5. Finishing: header liveness, comments, blocked badge, reconnection.
