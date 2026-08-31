"""tasklib — file-backed tickets in SHARED_DIR/tasks/, shared by `teams`, the board server and the hooks.

One ticket = one markdown file `T<n>.md`: a flat frontmatter (single-line values) and a body
made of `## <Section>` blocks. `## Log` is append-only and kept last. All writes are atomic
(tmp + os.replace); ids come from `.counter` under an exclusive flock, so the web UI and
gestion (via `teams task new`) share one collision-free sequence.
"""
import os, re, tempfile
from datetime import datetime
from pathlib import Path

STATUSES = ["backlog", "todo", "doing", "qa", "done"]
META_KEYS = ["id", "title", "team", "status", "blocked", "jira", "created", "updated", "by"]
_ID = re.compile(r"^T\d+$")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def tasks_dir(shared: Path) -> Path:
    d = Path(shared) / "tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _atomic_write(path: Path, text: str):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def alloc_id(shared: Path) -> str:
    """Next T<n>, atomic across processes (flock), never colliding with an existing file."""
    import fcntl
    d = tasks_dir(shared)
    with open(d / ".counter", "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        raw = fh.read().strip()
        n = int(raw) if raw.isdigit() else 0
        n += 1
        while (d / f"T{n}.md").exists():
            n += 1
        fh.seek(0)
        fh.truncate()
        fh.write(str(n))
        fh.flush()
        os.fsync(fh.fileno())
    return f"T{n}"


# ---------- parse / serialize ------------------------------------------------
def _clean(v) -> str:
    return " ".join(str(v).split())          # frontmatter values are single-line


def parse(path: Path) -> tuple[dict, str]:
    text = Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    meta, body = {}, text
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            k, sep, v = line.partition(":")
            if sep:
                meta[k.strip()] = v.strip()
    meta.setdefault("id", Path(path).stem)
    meta.setdefault("title", "(sans titre)")
    meta.setdefault("team", "-")
    meta["status"] = meta.get("status") if meta.get("status") in STATUSES else "backlog"
    meta["blocked"] = str(meta.get("blocked", "")).lower() == "true"
    meta.setdefault("jira", "")
    meta.setdefault("created", "")
    meta.setdefault("updated", "")
    meta.setdefault("by", "")
    return meta, body


def serialize(meta: dict, body: str) -> str:
    lines = []
    for k in META_KEYS:
        v = meta.get(k, "")
        if k == "blocked":
            v = "true" if v else "false"
        if k == "jira" and not v:
            continue
        lines.append(f"{k}: {_clean(v)}")
    for k, v in meta.items():                 # unknown keys (github:, linear:, …) survive round-trips
        if k not in META_KEYS:
            lines.append(f"{k}: {_clean(v)}")
    return "---\n" + "\n".join(lines) + "\n---\n\n" + body.strip() + "\n"


# ---------- body sections ----------------------------------------------------
def split_sections(body: str) -> list[tuple[str, str]]:
    """[('', preamble), ('Description', text), …] — heading order preserved."""
    parts, cur, buf = [], "", []
    for line in body.splitlines():
        h = re.match(r"^## (.+?)\s*$", line)
        if h:
            parts.append((cur, "\n".join(buf).strip()))
            cur, buf = h.group(1), []
        else:
            buf.append(line)
    parts.append((cur, "\n".join(buf).strip()))
    return [(t, x) for t, x in parts if t or x]


def get_section(body: str, name: str) -> str:
    for t, x in split_sections(body):
        if t.lower() == name.lower():
            return x
    return ""


def set_section(body: str, name: str, text: str) -> str:
    """Replace (or insert before Log) one section; drops it entirely when text is empty."""
    parts = split_sections(body)
    parts = [(t, x) for t, x in parts if t.lower() != name.lower()]
    if text.strip():
        i = next((i for i, (t, _) in enumerate(parts) if t.lower() == "log"), len(parts))
        parts.insert(i, (name, text.strip()))
    return join_sections(parts)


def join_sections(parts: list[tuple[str, str]]) -> str:
    out = []
    for t, x in parts:
        if t:
            out.append(f"## {t}")
        if x:
            out.append(x)
        out.append("")
    return "\n".join(out).strip() + "\n"


def log_entries(body: str) -> list[str]:
    return [l[2:].strip() for l in get_section(body, "Log").splitlines() if l.startswith("- ")]


# ---------- high-level operations -------------------------------------------
def path_of(shared: Path, tid: str) -> Path:
    if not _ID.fullmatch(tid):
        raise ValueError(f"bad ticket id: {tid}")
    return tasks_dir(shared) / f"{tid}.md"


def load(shared: Path, tid: str) -> dict:
    meta, body = parse(path_of(shared, tid))
    return to_dict(meta, body)


def load_all(shared: Path) -> list[dict]:
    out = []
    for p in sorted(tasks_dir(shared).glob("T*.md"), key=lambda p: int(p.stem[1:]) if p.stem[1:].isdigit() else 0):
        try:
            meta, body = parse(p)
            out.append(to_dict(meta, body))
        except (OSError, ValueError):
            out.append({"id": p.stem, "title": f"⚠ fichier illisible ({p.name})", "team": "-", "status": "backlog",
                        "blocked": False, "jira": "", "created": "", "updated": "", "by": "",
                        "description": "", "criteria": "", "log": [], "broken": True})
    return out


def to_dict(meta: dict, body: str) -> dict:
    return {**meta,
            "description": get_section(body, "Description"),
            "criteria": get_section(body, "Criteria"),
            "log": log_entries(body)}


def create(shared: Path, title: str, *, team: str = "-", status: str = "backlog", jira: str = "",
           description: str = "", criteria: str = "", by: str = "human") -> dict:
    if status not in STATUSES:
        raise ValueError(f"bad status: {status}")
    tid = alloc_id(shared)
    meta = {"id": tid, "title": _clean(title) or "(sans titre)", "team": _clean(team) or "-", "status": status,
            "blocked": False, "jira": _clean(jira), "created": now(), "updated": now(), "by": by}
    body = ""
    if description.strip():
        body = set_section(body, "Description", description)
    if criteria.strip():
        body = set_section(body, "Criteria", criteria)
    body = set_section(body, "Log", f"- {datetime.now():%H:%M:%S} created by {by} ({status})")
    _atomic_write(path_of(shared, tid), serialize(meta, body))
    return to_dict(meta, body)


def update(shared: Path, tid: str, changes: dict) -> dict:
    """Apply meta changes (title/team/status/blocked/jira/…) and description/criteria rewrites."""
    p = path_of(shared, tid)
    meta, body = parse(p)
    for k, v in changes.items():
        if k in ("description", "criteria"):
            body = set_section(body, k.capitalize(), str(v))
        elif k == "blocked":
            meta[k] = v if isinstance(v, bool) else str(v).lower() == "true"
        elif k == "status":
            if v not in STATUSES:
                raise ValueError(f"bad status: {v}")
            meta[k] = v
        elif k == "id":
            continue
        else:
            meta[k] = _clean(v)
    meta["updated"] = now()
    _atomic_write(p, serialize(meta, body))
    return to_dict(meta, body)


def append_log(shared: Path, tid: str, text: str) -> dict:
    p = path_of(shared, tid)
    meta, body = parse(p)
    log = get_section(body, "Log")
    entry = f"- {datetime.now():%H:%M:%S} {_clean(text)}"
    body = set_section(body, "Log", (log + "\n" + entry).strip())
    meta["updated"] = now()
    _atomic_write(p, serialize(meta, body))
    return to_dict(meta, body)


def delete(shared: Path, tid: str):
    path_of(shared, tid).unlink(missing_ok=True)


def apply_message(shared: Path, sender: str, to: str, header: str) -> list[str]:
    """Mirror one inter-team message (`TYPE T3[,T4] | what`) into the tickets it references.

    Called by the SendMessage hook — costs no tokens. Rules:
      TASK    → status doing (from backlog/todo), team = recipient
      DONE    → status qa (from doing), blocked cleared
      BLOCKED → blocked flag set
    Every match also gets the header appended to its ## Log. Returns touched ids.
    """
    m = re.match(r"\s*([A-Z]+)\b", header)
    typ = m.group(1) if m else ""
    touched = []
    for tid in dict.fromkeys(re.findall(r"\bT\d+\b", header)):
        if not path_of(shared, tid).exists():
            continue
        append_log(shared, tid, f"{sender} → {to} | {header.strip()}")
        cur = load(shared, tid)
        if typ == "TASK" and cur["status"] in ("backlog", "todo"):
            update(shared, tid, {"status": "doing", "team": to})
        elif typ == "DONE":
            update(shared, tid, {"blocked": False, **({"status": "qa"} if cur["status"] == "doing" else {})})
        elif typ == "BLOCKED":
            update(shared, tid, {"blocked": True})
        touched.append(tid)
    return touched


def summary(shared: Path) -> str:
    """Compact per-status counts + one line per open ticket (for `teams status`)."""
    ts = load_all(shared)
    if not ts:
        return "tasks: none yet"
    by = {}
    for t in ts:
        by[t["status"]] = by.get(t["status"], 0) + 1
    head = "tasks: " + ", ".join(f"{by[s]} {s}" for s in STATUSES if s in by)
    rows = [f"{t['id']:4} [{t['team']}] {t['status']:7}{' ⛔' if t['blocked'] else '  '} {t['title'][:56]}"
            + (f"  ({t['jira']})" if t["jira"] else "")
            for t in ts if t["status"] != "done"]
    return head + ("\n  " + "\n  ".join(rows) if rows else "")
