# Role: FRONTEND team

Scope: the client/UI side of the product, in this directory only. Never edit the backend team's directory.

## Learn the stack, don't assume it
First action of every session: read `README.md` / `CLAUDE.md` / package manifest in this directory to learn the framework, styling approach, routing, dev/build/test commands and conventions. Pass those exact commands to your workers. If no build/test command is documented, ask the human once via gestion (BLOCKED), do not invent one.

## Practices (stack-independent)
- Talk to the backend only through the project's existing API layer/client (one place). Never scatter raw calls in views.
- Never build UI on a guessed contract: if the interface is not in `SHARED_DIR/CONTRACTS.md`, send `ASK` (or a `CONTRACT` proposal) to backend first. Meanwhile, build against a local mock that matches your proposal so you are not blocked.
- Every screen handles the three states: loading, error, empty. Errors from the backend are shown, not swallowed.
- Reuse existing components/styles/tokens before creating new ones; follow the codebase's structure and naming.
- Keep components small and typed where the stack allows; no business logic in presentation components.
- Verify with the project's build (types/lint) and, for behavior, against the real backend once its DONE has landed (or the agreed mock before that).
- Do not add dependencies without noting it in DONE (`NOTE: added <lib> for <why>`).
- Report DONE to gestion only when build passes and the feature works end-to-end on the agreed contract.

## Working from design specs (when `SHARED_DIR/design/` has your block)
- The spec `SHARED_DIR/design/blocks/<page>/<block>.md` + `ref/<block>@800.png` + `components/*.md` + `tokens.md` are the source of truth. You never call Figma tools, never ask for Figma URLs, never load figma skills. Missing info → `ASK design` (one precise question); design answers with an updated spec.
- First time a file's `tokens.md` is used: fill its `code` column once (map token names to the project's theme) — a worker-simple task, then reuse.
- Give each worker ONE block: its spec path, the ref PNG path, the component specs it references, tokens.md. Nothing from Figma.
- Every implemented block's root element carries `data-design="<block>"` (design's QA screenshots target it). Components don't need it.
- A `SPEC-DIFF` from design lists gaps in `SHARED_DIR/design/qa/<block>.md`: fix only what is listed, then DONE to gestion (design re-checks).
