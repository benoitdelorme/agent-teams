# use_figma — the rules that matter here (read this, not the figma-use skill)

1. Plain JS, top-level `await`, `return` the result (JSON-serialised). No `figma.closePlugin()`, no async IIFE, no `console.log` (not returned), no `figma.notify()` (throws).
2. A script that throws is **atomic**: nothing it did is applied. Use `throw new Error("<nodeId>: <reason>")` as the rollback mechanism.
3. Page context resets every call. Switch with `await figma.setCurrentPageAsync(page)` — **at most once per script**; `figma.currentPage = page` throws.
4. `await figma.getNodeByIdAsync(id)` for any id (sync `getNodeById` may return null for unloaded pages). Ids use `:` (`12:34`).
5. Colors are 0–1 (`{r:1,g:0,b:0}`); `fills`/`strokes` are read-only arrays → clone, edit, reassign.
6. Text: any mutation of a TEXT node (characters, appendChild into it, bound vars) needs its fonts loaded first: `for (const f of node.getRangeAllFontNames(0, node.characters.length)) await figma.loadFontAsync(f)`. Inter style names: "Semi Bold", "Extra Bold" (with space).
7. Auto-layout enums — two different ones:
   - on the **container**: `layoutMode: 'NONE'|'HORIZONTAL'|'VERTICAL'`, `primaryAxisSizingMode`/`counterAxisSizingMode: 'FIXED'|'AUTO'`, `itemSpacing`, `paddingLeft/Right/Top/Bottom`, `primaryAxisAlignItems: 'MIN'|'CENTER'|'MAX'|'SPACE_BETWEEN'`, `counterAxisAlignItems: 'MIN'|'CENTER'|'MAX'|'BASELINE'`, `layoutWrap: 'NO_WRAP'|'WRAP'`.
   - on a **child** of an auto-layout frame: `layoutSizingHorizontal/Vertical: 'FIXED'|'HUG'|'FILL'` (`FILL` only for children of auto-layout, `HUG` only for auto-layout frames or TEXT) and `layoutPositioning: 'AUTO'|'ABSOLUTE'`. Set these AFTER the child is inside an auto-layout parent, never before.
8. Converting a frame to auto-layout re-flows its children immediately. To keep the visual identical: set `layoutMode`, keep both sizing modes `FIXED`, set paddings = min offsets, `itemSpacing` = the uniform gap, alignment matching the children, then re-append children in visual order. Verify with bounding boxes, not by eye.
9. Cannot restructure inside an INSTANCE (children are locked to the main component); can set layout props on the instance's own container only if it is a frame you own. GROUP nodes have no auto-layout: leave them or wrap them (structure change — report it).
10. `absoluteBoundingBox` is in canvas space (null for invisible/empty nodes); subtract the root's box to compare two nodes. `x/y` are relative to the parent.
11. New page-level nodes land at (0,0): place copies to the right of the rightmost node (`Math.max(...page.children.map(n => n.x + n.width)) + 200`).
12. `node.clone()` keeps the same parent; `page.appendChild(clone)` moves it. Inside the copy, ids are new — never reuse the original's ids after cloning.
13. Unsupported in this tool: `loadAllPagesAsync`, `setPluginData`, `createImageAsync`. Don't.
14. Keep scripts small and return every created/mutated id (`{createdNodeIds, mutatedNodeIds}`) so the next call can target or clean them.
15. Groups have no auto-layout: autolayout.js turns them into frames (same bbox) before converting; masks inside a group block that step.
