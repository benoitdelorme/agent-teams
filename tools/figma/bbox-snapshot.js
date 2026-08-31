// bbox-snapshot.js — {leafId: [x,y,w,h]} of every visible leaf, relative to the node. Edit PARAMS only.
// Compare two snapshots (original vs copy) by matching leaves in traversal order: ids differ after clone, order does not.
const PARAMS = { nodeId: "0:0" };

const root = await figma.getNodeByIdAsync(PARAMS.nodeId);
if (!root) throw new Error(PARAMS.nodeId + ": node not found");
const rb = root.absoluteBoundingBox;
if (!rb) throw new Error(PARAMS.nodeId + ": no bounding box (hidden or empty)");
const leaves = [];
const walk = (n) => {
  if (n.visible === false) return;
  const kids = "children" in n && n.type !== "INSTANCE" ? n.children : [];
  if (!kids.length) {
    const b = n.absoluteBoundingBox;
    if (b) leaves.push([n.id, n.name.slice(0, 30), +(b.x - rb.x).toFixed(1), +(b.y - rb.y).toFixed(1), +b.width.toFixed(1), +b.height.toFixed(1)]);
    return;
  }
  for (const c of kids) walk(c);
};
walk(root);
return { root: PARAMS.nodeId, size: [Math.round(rb.width), Math.round(rb.height)], leaves };
