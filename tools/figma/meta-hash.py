#!/usr/bin/env python3
"""meta-hash.py <page.xml> [--ids a:b,c:d] [--depth N]
Hash each block's subtree from a `get_metadata` XML dump (structure + names + boxes) → 8 hex chars.
Zero LLM tokens. Default: hash every direct child of the root element. Tolerant to the exact tag/attribute names."""
import hashlib, re, sys, xml.etree.ElementTree as ET

def canon(el, depth, max_depth):
    a = el.attrib
    box = ",".join(str(round(float(a.get(k, 0)))) for k in ("x", "y", "width", "height") if a.get(k) not in (None, ""))
    s = f"{el.tag}|{a.get('name', '')}|{a.get('type', '')}|{box}|{a.get('layoutMode', a.get('layout', ''))}"
    if depth < max_depth:
        s += "(" + ";".join(canon(c, depth + 1, max_depth) for c in el) + ")"
    return s

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    path, ids, depth = args[0], None, 6
    if "--ids" in args:
        ids = [x.strip().replace("-", ":") for x in args[args.index("--ids") + 1].split(",") if x.strip()]
    if "--depth" in args:
        depth = int(args[args.index("--depth") + 1])
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"^.*?(?=<)", "", text, count=1, flags=re.S)          # strip any prose before the XML
    root = ET.fromstring(text)
    by_id = {}
    for el in root.iter():
        i = el.attrib.get("id") or el.attrib.get("guid") or el.attrib.get("nodeId")
        if i:
            by_id[i.replace("-", ":")] = el
    targets = [(i, by_id.get(i)) for i in ids] if ids else [(c.attrib.get("id", "?"), c) for c in (root if len(root) else [root])]
    for i, el in targets:
        print(f"{i}\t{hashlib.sha1(canon(el, 0, depth).encode()).hexdigest()[:8] if el is not None else 'not-found'}")

if __name__ == "__main__":
    main()
