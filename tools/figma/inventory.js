// inventory.js — flat compact tree of a node for use_figma. Edit PARAMS only.
const PARAMS = { nodeId: "0:0", maxDepth: 3, includeHidden: false };

const root = await figma.getNodeByIdAsync(PARAMS.nodeId);
if (!root) throw new Error(PARAMS.nodeId + ": node not found");
const rb = root.absoluteBoundingBox || { x: 0, y: 0 };
const rows = [];
const kind = (n) => n.type === "INSTANCE" ? "inst" : n.type === "COMPONENT" ? "comp" : n.type === "TEXT" ? "text" : n.type === "GROUP" ? "group" : "";
const walk = (n, depth) => {
  if (!PARAMS.includeHidden && n.visible === false) return;
  const b = n.absoluteBoundingBox;
  rows.push([n.id, n.name.slice(0, 40), n.type, depth,
    b ? Math.round(b.x - rb.x) : null, b ? Math.round(b.y - rb.y) : null, b ? Math.round(b.width) : null, b ? Math.round(b.height) : null,
    "layoutMode" in n ? n.layoutMode : "-", kind(n)]);
  if (depth < PARAMS.maxDepth && "children" in n && n.type !== "INSTANCE") for (const c of n.children) walk(c, depth + 1);
};
walk(root, 0);
// columns: id, name, type, depth, x, y, w, h (relative to root), layoutMode, kind
return { columns: ["id", "name", "type", "depth", "x", "y", "w", "h", "layout", "kind"], rows };
