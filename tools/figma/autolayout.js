// autolayout.js — convert an absolutely-positioned block to auto-layout, on a COPY, self-verified, atomic.
// Worker edits PARAMS only. Throws (= full rollback by Figma) whenever a conversion would move or resize any node (container or leaf) by more than `tol`.
// Report: { copyId, page, converted: [id], skipped: [{id, name, reason}], leaves, nodes, maxDelta, reordered: [id], groupsToFrames: [id] }
const PARAMS = {
  nodeId: "0:0",          // original block (never modified)
  pageName: "_autolayout",
  tol: 1,                 // px tolerance on bounding boxes (containers and leaves)
  skip: [],               // container ids (in the COPY, from a previous run's error) left as-is
  maxAbsolute: 2,         // max overlapping children per container turned ABSOLUTE before giving up
  groupsToFrames: true,   // GROUPs (root included) become plain frames of the same bbox first — groups cannot have auto-layout
};

// ---------- helpers ----------
const near = (a, b, t = PARAMS.tol) => Math.abs(a - b) <= t;
const box = (n) => ({ x: n.x, y: n.y, w: n.width, h: n.height, r: n.x + n.width, b: n.y + n.height });
const disjoint = (a, b, axis, t = PARAMS.tol) => axis === "V" ? (a.b <= b.y + t || b.b <= a.y + t) : (a.r <= b.x + t || b.r <= a.x + t);
const allDisjoint = (items, axis) => items.every((a, i) => items.every((b, j) => i === j || disjoint(a.box, b.box, axis)));
const overlaps = (a, b) => !(a.r <= b.x || b.r <= a.x || a.b <= b.y || b.b <= a.y);
const isContainer = (n) => (n.type === "FRAME" || n.type === "COMPONENT") && "layoutMode" in n;
const nodesOf = (root) => {                                                    // every visible node with a bbox: containers AND leaves (last field = leaf?)
  const out = [];
  const walk = (n) => {
    if (n.visible === false) return;
    const kids = "children" in n && n.type !== "INSTANCE" ? n.children : [];
    const b = n.absoluteBoundingBox; if (b) out.push([n.id, b.x, b.y, b.width, b.height, !kids.length]);
    for (const c of kids) walk(c);
  };
  walk(root); return out;
};
const snapshot = (root) => { const rb = root.absoluteBoundingBox; return nodesOf(root).map(([id, x, y, w, h, leaf]) => [id, x - rb.x, y - rb.y, w, h, leaf]); };
const compare = (before, after, ignoreMissing = false) => {                    // ignoreMissing: only for group→frame, where ids legitimately change
  const m = new Map(after.map((l) => [l[0], l]));
  let max = 0, worst = null;
  for (const l of before) {
    const a = m.get(l[0]); if (!a) { if (ignoreMissing) continue; return { max: Infinity, worst: l[0] + " missing" }; }
    const d = Math.max(Math.abs(a[1] - l[1]), Math.abs(a[2] - l[2]), Math.abs(a[3] - l[3]), Math.abs(a[4] - l[4]));
    if (d > max) { max = d; worst = l[0]; }
  }
  return { max, worst };
};

// ---------- 1. copy onto _autolayout ----------
const src = await figma.getNodeByIdAsync(PARAMS.nodeId);
if (!src) throw new Error(PARAMS.nodeId + ": node not found");
if (!isContainer(src) && src.type !== "SECTION" && !(PARAMS.groupsToFrames && src.type === "GROUP")) throw new Error(PARAMS.nodeId + ": not a frame/component (" + src.type + ")");
let page = figma.root.children.find((p) => p.name === PARAMS.pageName);
if (!page) { page = figma.createPage(); page.name = PARAMS.pageName; }
await figma.setCurrentPageAsync(page);
let copy = src.clone();
page.appendChild(copy);
copy.name = src.name + " (autolayout)";
const others = page.children.filter((n) => n !== copy);
copy.x = others.length ? Math.max(...others.map((n) => n.x + n.width)) + 200 : 0;
copy.y = others.length ? Math.min(...others.map((n) => n.y)) : 0;
let before = snapshot(copy);
const report = { copyId: copy.id, page: PARAMS.pageName, converted: [], skipped: [], reordered: [], groupsToFrames: [], leaves: before.filter((l) => l[5]).length, nodes: before.length, maxDelta: 0 };
const skipSet = new Set(PARAMS.skip);
const skip = (n, reason) => { report.skipped.push({ id: n.id, name: n.name.slice(0, 30), reason }); };

// ---------- 1b. groups → frames (same bbox, same leaves), top-down so a group's parent is always a frame/page ----------
if (PARAMS.groupsToFrames) {
  const groupToFrame = (g) => {
    const parent = g.parent, idx = parent.children.indexOf(g);
    const f = figma.createFrame();
    f.name = g.name; f.fills = []; f.clipsContent = false; f.layoutMode = "NONE";
    parent.insertChild(idx, f);
    f.x = g.x; f.y = g.y; f.resizeWithoutConstraints(g.width, g.height);
    const fx = f.absoluteTransform[0][2], fy = f.absoluteTransform[1][2];
    for (const k of [...g.children]) {                                         // appendChild keeps x/y verbatim → re-derive them from the absolute position
      const t = k.absoluteTransform;
      f.appendChild(k); k.x = t[0][2] - fx; k.y = t[1][2] - fy;
    }
    if (!g.removed) g.remove();                                                // Figma drops an emptied group on its own
    return f;
  };
  const convertGroups = (n) => {
    if (n.type === "INSTANCE") return n;
    if (n.type === "GROUP") {
      if (n.children.some((k) => k.isMask)) { skip(n, "group with mask"); return n; }   // untouched, not descended
      n = groupToFrame(n); report.groupsToFrames.push(n.id);
    }
    if ("children" in n) for (const k of [...n.children]) convertGroups(k);
    return n;
  };
  copy = convertGroups(copy);
  report.copyId = copy.id;
  const { max, worst } = compare(before, snapshot(copy), true);
  if (max > PARAMS.tol) throw new Error(copy.id + ": group→frame moved node " + worst + " by " + max.toFixed(1) + "px");
  before = snapshot(copy);                                                     // re-baseline: new frame ids replace group ids, so step 3 can require every id
}

// ---------- 2. convert one container (throws on failure) ----------

function plan(c) {
  const kids = c.children.filter((k) => k.visible !== false);
  if (!kids.length) return { reason: "empty" };
  if (kids.some((k) => k.rotation && !near(k.rotation, 0, 0.01))) return { reason: "rotated child" };
  let items = kids.map((k) => ({ node: k, box: box(k), abs: false }));
  // overlapping children → ABSOLUTE (backgrounds, badges, decor), at most maxAbsolute of them
  let axis = null, absCount = 0;
  while (true) {
    const flow = items.filter((i) => !i.abs);
    if (allDisjoint(flow, "V")) { axis = "V"; break; }
    if (allDisjoint(flow, "H")) { axis = "H"; break; }
    if (absCount >= PARAMS.maxAbsolute) return { reason: "overlapping children (>" + PARAMS.maxAbsolute + ")" };
    // pick the non-text child with most overlaps (a full-size background first)
    const scored = flow.map((i) => ({ i, n: flow.filter((o) => o !== i && overlaps(i.box, o.box)).length, full: near(i.box.w, c.width, 2) && near(i.box.h, c.height, 2), text: i.node.type === "TEXT" }))
      .sort((a, b) => (b.full - a.full) || (a.text - b.text) || (b.n - a.n));
    if (!scored.length || scored[0].n === 0) return { reason: "unresolvable overlap" };
    scored[0].i.abs = true; absCount++;
  }
  const flow = items.filter((i) => !i.abs).sort((a, b) => axis === "V" ? a.box.y - b.box.y : a.box.x - b.box.x);
  if (flow.length === 0) return { reason: "no flow children" };
  // gaps must be uniform
  const gaps = [];
  for (let i = 1; i < flow.length; i++) gaps.push(axis === "V" ? flow[i].box.y - flow[i - 1].box.b : flow[i].box.x - flow[i - 1].box.r);
  if (gaps.length && Math.max(...gaps) - Math.min(...gaps) > PARAMS.tol) return { reason: "irregular gaps " + gaps.map((g) => Math.round(g)).join("/") };
  const gap = gaps.length ? gaps.reduce((a, b) => a + b, 0) / gaps.length : 0;
  const minX = Math.min(...flow.map((i) => i.box.x)), minY = Math.min(...flow.map((i) => i.box.y));
  const maxR = Math.max(...flow.map((i) => i.box.r)), maxB = Math.max(...flow.map((i) => i.box.b));
  const pad = { l: minX, t: minY, r: c.width - maxR, b: c.height - maxB };
  if (Math.min(pad.l, pad.t, pad.r, pad.b) < -PARAMS.tol) return { reason: "child overflows container" };
  // counter-axis alignment must be consistent across flow children
  const alignOf = (i) => {
    if (axis === "V") { if (near(i.box.x, pad.l)) return "MIN"; if (near(i.box.r, c.width - pad.r)) return "MAX"; if (near(i.box.x + i.box.w / 2, c.width / 2)) return "CENTER"; }
    else { if (near(i.box.y, pad.t)) return "MIN"; if (near(i.box.b, c.height - pad.b)) return "MAX"; if (near(i.box.y + i.box.h / 2, c.height / 2)) return "CENTER"; }
    return null;
  };
  const aligns = new Set(flow.map(alignOf));
  if (aligns.has(null)) return { reason: "child neither start/center/end aligned on counter axis" };
  let align = aligns.size === 1 ? [...aligns][0] : aligns.has("MIN") ? "MIN" : null;   // MIN + full-width FILL children is still consistent
  if (!align) return { reason: "mixed counter-axis alignment " + [...aligns].join("/") };
  if (aligns.size > 1) for (const i of flow) if (alignOf(i) !== "MIN" && !(axis === "V" ? near(i.box.w, c.width - pad.l - pad.r) : near(i.box.h, c.height - pad.t - pad.b))) return { reason: "mixed counter-axis alignment" };
  return { axis, gap, pad, align, flow, abs: items.filter((i) => i.abs) };
}

function apply(c, p) {
  const w = c.width, h = c.height;
  c.layoutMode = p.axis === "V" ? "VERTICAL" : "HORIZONTAL";                 // this alone hugs the children (sizing defaults to AUTO) → the frame shrinks
  c.primaryAxisSizingMode = "FIXED"; c.counterAxisSizingMode = "FIXED";     // never let the container resize
  c.itemSpacing = p.gap; c.paddingLeft = p.pad.l; c.paddingTop = p.pad.t; c.paddingRight = p.pad.r; c.paddingBottom = p.pad.b;
  if (c.width !== w || c.height !== h) c.resizeWithoutConstraints(w, h);     // restore the pre-conversion size
  c.primaryAxisAlignItems = "MIN"; c.counterAxisAlignItems = p.align;
  for (const i of p.abs) { i.node.layoutPositioning = "ABSOLUTE"; i.node.x = i.box.x; i.node.y = i.box.y; }
  for (const i of p.flow) { c.appendChild(i.node); }                          // visual order = layout order
  const inner = p.axis === "V" ? c.width - p.pad.l - p.pad.r : c.height - p.pad.t - p.pad.b;
  for (const i of p.flow) {                                                    // full-width/height children become FILL (same size today, responsive tomorrow)
    if (p.axis === "V" && near(i.box.w, inner)) i.node.layoutSizingHorizontal = "FILL";
    if (p.axis === "H" && near(i.box.h, inner)) i.node.layoutSizingVertical = "FILL";
  }
  if (p.abs.length) report.reordered.push(c.id);
}

// ---------- 3. walk top-down ----------
const queue = [copy];
while (queue.length) {
  const c = queue.shift();
  if (c.type === "INSTANCE") continue;                                         // cannot restructure inside instances
  if (isContainer(c) && c.layoutMode === "NONE" && !skipSet.has(c.id)) {
    const p = plan(c);
    if (p.reason) skip(c, p.reason);
    else {
      apply(c, p);
      const { max, worst } = compare(before, snapshot(copy));
      if (max > PARAMS.tol) throw new Error(c.id + ": conversion moved/resized node " + worst + " by " + max.toFixed(1) + "px — add this id to PARAMS.skip and re-run");
      report.converted.push(c.id); report.maxDelta = Math.max(report.maxDelta, max);
    }
  } else if (c.type === "GROUP") skip(c, "group (no auto-layout on groups)");
  if ("children" in c) for (const k of c.children) if ("children" in k) queue.push(k);
}
return report;
