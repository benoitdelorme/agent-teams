# Inter-team communication protocol

Goal: minimum tokens, zero ambiguity. Silence is the default. A message costs; only send when it changes what the recipient will do.

## Channel
1. Primary: `SendMessage({to: "<team>", message})` — `to` is exactly the session name from ROSTER (bare team name, or `<session_prefix>-<team>` when the config sets a prefix — the ROSTER then lists `session=` per team); confirm once with `ListAgents` at start.
2. Fallback (only if SendMessage errors): `{{teams}} msg <team> "<text>"` types the line into that team's terminal. If that fails too, tell the human.
Never use both for the same message.

## Message format — one message = one line header + optional body
```
<TYPE> <ref> | <what>            ← header, mandatory, ≤ 100 chars
<body>                           ← optional, ≤ 5 lines, only facts the recipient needs
```
`<ref>` = ticket id from `SHARED_DIR/tasks/` (T3), or `-` if none. Batch refs comma-separated (`DONE T1,T2 | …`).

Types (the only ones allowed):
| TYPE      | sender → recipient           | when                                             | reply expected     |
|-----------|------------------------------|--------------------------------------------------|--------------------|
| TASK      | manager → team               | assign work. Body: none (criteria live in the ticket); at most an ordering note. | DONE or BLOCKED    |
| DONE      | team → manager               | task meets criteria. Body: changed paths, verify.| none               |
| BLOCKED   | team → manager               | can't proceed. Body: exact missing thing.        | TASK / ANSWER      |
| ASK       | any → any                    | one precise question. Body: options if any.      | ANSWER             |
| ANSWER    | any → any                    | reply to ASK. Body: the answer, nothing else.    | none               |
| CONTRACT  | team ↔ team                  | API shape proposal/agreement. Body: pointer to `SHARED_DIR/CONTRACTS.md` section + 1-line diff summary. | ANSWER (`agree` / objection) |
| STATUS    | manager → any (rare)         | request state. Body: none.                       | one-line answer    |

## Hard rules
- No greetings, no thanks, no "received", no recap of what the other said. Silence = ack.
- Never paste code in a message. Point to `path:line` or a section of `SHARED_DIR/CONTRACTS.md`.
- Never send the same info to two teams "for information". Send only to who acts on it. manager learns via DONE/BLOCKED, not CC.
- One message per state change. Batch: if 3 tasks finish together, one DONE listing T1,T2,T3.
- Do not reply to DONE, ANSWER, or STATUS answers.
- Detail lives in files, not messages: tasks in `SHARED_DIR/tasks/T<n>.md`, API shapes in `SHARED_DIR/CONTRACTS.md`. Update the file, then send the 1-line pointer.
- Messages whose header carries a `T<n>` ref are mirrored into that ticket's `## Log` (and TASK/DONE/BLOCKED update its status/flags) by successful PostToolUse hooks. Failed sends leave ticket state unchanged. A synchronization warning after a successful send requires checking the recorded event before retrying. Never send a message whose only purpose is a status update.
- Do not poll. Replies arrive as new turns in your session; end your turn and wait. STATUS at most once per task, only if a DONE/BLOCKED is overdue.
- Language: messages between teams in English (denser). Talk to the human in {{language}}.

## Examples
```
TASK T2 | POST /api/projects/{id}/archive — see tasks/T2.md
after T1 (schema); contract goes to SHARED_DIR/CONTRACTS.md#archive
```
```
DONE T2 | src/api/projects.*:140-152, tests/projects_test.*:31 — test suite green
```
```
BLOCKED T4 | need archived field in Project schema (backend T2 not done)
```
```
CONTRACT T4 | shared/CONTRACTS.md#archive — added `archived: bool` to Project
```
```
ANSWER T4 | agree
```

Message reference IDs belong before `|`; IDs mentioned in the summary do not change other tickets. The terminal fallback does not trigger SendMessage hooks: report a failed delivery explicitly.
