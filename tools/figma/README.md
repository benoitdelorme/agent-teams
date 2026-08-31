# tools/figma — canonical Figma tooling (read on demand, never injected)

Workers `Read` these files when their prompt says so. Nothing here is loaded into a system prompt.

| file | used by | how | in → out |
|---|---|---|---|
| `gotchas.md` | design-autolayout (and anyone touching `use_figma`) | read before running a script | the ~10 Plugin API rules that matter here; replaces the 9k-token `figma-use` skill |
| `spec-template.md` | design-extract, design-vision | read before writing/reading a spec | block/component spec format |
| `inventory.js` | any (debug, split when XML is ambiguous) | `use_figma` with PARAMS filled | node id → flat compact tree `[id, name, type, x, y, w, h, layoutMode, kind]` |
| `bbox-snapshot.js` | design-autolayout, design-vision (numeric check) | `use_figma` | node id → `{leafId: [x,y,w,h]}` relative to the node |
| `autolayout.js` | design-autolayout | `use_figma`; fill `PARAMS` only | node id → copy on `_autolayout`, converted top-down, self-verified, atomic; returns report |
| `meta-hash.py` | design-split | `python3 meta-hash.py <page.xml> --ids a,b` | `get_metadata` XML → 8-char hash per block (structure + boxes) |

Conventions shared by the `.js` scripts:
- top-of-file `const PARAMS = {...}` is the only thing a worker edits;
- plain JS, top-level `await`, end with `return <json>` (the harness serialises it);
- one `figma.setCurrentPageAsync` per run at most;
- scripts THROW on any doubt → the whole run is rolled back by Figma (atomic). The error message names the node id and reason so the worker can add it to `PARAMS.skip`.

Statuses in `shared/design/MANIFEST.md`: `todo → autolayout → extracted → implemented → qa-ok | qa-diff`, `stale` when `meta-hash` changed.
