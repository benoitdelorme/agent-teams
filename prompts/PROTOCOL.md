# Inter-team communication protocol

Goal: minimum tokens, zero ambiguity. Silence is the default. A message costs; only send when it changes what the recipient will do.

## Channel
1. Primary: `SendMessage({to: "<team>", message})` — team names come from ROSTER. Confirm names once with `ListAgents` at start (match by prefix if suffixed).
2. Fallback (only if SendMessage errors): `programa send --surface <surface> "<text>\n"` using surfaces from `shared/.roster.json`.
Never use both for the same message.

## Message format — one message = one line header + optional body
```
<TYPE> <ref> | <what>            ← header, mandatory, ≤ 100 chars
<body>                           ← optional, ≤ 5 lines, only facts the recipient needs
```
`<ref>` = task id from `shared/PLAN.md` (T3), or `-` if none.

Types (the only ones allowed):
| TYPE      | sender → recipient           | when                                             | reply expected     |
|-----------|------------------------------|--------------------------------------------------|--------------------|
| TASK      | gestion → team               | assign work. Body: acceptance criteria only.     | DONE or BLOCKED    |
| DONE      | team → gestion               | task meets criteria. Body: changed paths, verify.| none               |
| BLOCKED   | team → gestion               | can't proceed. Body: exact missing thing.        | TASK / ANSWER      |
| ASK       | any → any                    | one precise question. Body: options if any.      | ANSWER             |
| ANSWER    | any → any                    | reply to ASK. Body: the answer, nothing else.    | none               |
| CONTRACT  | frontend ↔ backend           | API shape proposal/agreement. Body: pointer to `shared/CONTRACTS.md` section + 1-line diff summary. | ANSWER (`agree` / objection) |
| STATUS    | gestion → any (rare)         | request state. Body: none.                       | one-line answer    |
| SPEC      | design → frontend            | specs ready. Body: pointer to `shared/design/MANIFEST.md` (+ blocks/components list). | none |
| SPEC-DIFF | design → frontend            | visual QA gaps. Body: pointer to `shared/design/qa/<block>.md` per block + count. | DONE (fix) |

## Hard rules
- No greetings, no thanks, no "received", no recap of what the other said. Silence = ack.
- Never paste code in a message. Point to `path:line` or a section of `shared/CONTRACTS.md`.
- Never send the same info to two teams "for information". Send only to who acts on it. gestion learns via DONE/BLOCKED, not CC.
- One message per state change. Batch: if 3 tasks finish together, one DONE listing T1,T2,T3.
- Do not reply to DONE, ANSWER, or STATUS answers.
- Detail lives in files, not messages: plan/status in `shared/PLAN.md`, API shapes in `shared/CONTRACTS.md`. Update the file, then send the 1-line pointer.
- Do not poll. Replies arrive as new turns in your session; end your turn and wait. STATUS at most once per task, only if a DONE/BLOCKED is overdue.
- Language: messages in English (denser). Talk to the human in French.

## Examples
```
TASK T2 | POST /api/projects/{id}/archive, sets archived=1, 404 if missing
criteria: endpoint + test; contract in shared/CONTRACTS.md#archive
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
```
SPEC D1 | shared/design/MANIFEST.md — pricing: 7 blocks, 3 components (Button, Card, Badge)
```
```
SPEC-DIFF F3 | shared/design/qa/plan-cards.md — 4 diffs (2 high)
```
