"""tasklib — file-backed tickets in SHARED_DIR/tasks/, shared by `teams`, the board server and the hooks.

One ticket = one markdown file `T<n>.md`: a flat frontmatter (single-line values) and a body
made of `## <Section>` blocks. All read/modify/write operations take the same local
lock; replacement is atomic. CLI, hooks and board share validation and history.
"""
import re
import storage
from datetime import datetime
from pathlib import Path

STATUSES = ["backlog", "todo", "doing", "qa", "done"]
META_KEYS = ["id", "title", "team", "status", "blocked", "ref", "created", "updated", "by"]
_ID = re.compile(r"^T\d+$")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def tasks_dir(shared: Path) -> Path:
    d = Path(shared) / "tasks"
    d.mkdir(parents=True, exist_ok=True)
    return d


_atomic_write = storage.atomic_write


def lock(shared):
    return storage.locked(Path(shared) / ".locks" / "tasks.lock")


def alloc_id(shared: Path) -> str:
    """Called while holding the shared task lock."""
    d = tasks_dir(shared)
    counter = d / '.counter'
    n = int(counter.read_text() or '0') if counter.exists() else 0
    n += 1
    while (d / f'T{n}.md').exists():
        n += 1
    _atomic_write(counter, str(n))
    return f'T{n}'


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
    meta.setdefault("title", "(untitled)")
    meta.setdefault("team", "-")
    meta["status"] = meta.get("status") if meta.get("status") in STATUSES else "backlog"
    meta["blocked"] = str(meta.get("blocked", "")).lower() == "true"
    meta.setdefault("ref", meta.pop("jira", ""))      # `jira:` in older tickets is read as `ref`
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
        if k == "ref" and not v:
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
            out.append({"id": p.stem, "title": f"⚠ unreadable file ({p.name})", "team": "-", "status": "backlog",
                        "blocked": False, "ref": "", "created": "", "updated": "", "by": "",
                        "description": "", "criteria": "", "log": [], "broken": True})
    return out


def to_dict(meta: dict, body: str) -> dict:
    return {**meta,
            "description": get_section(body, "Description"),
            "criteria": get_section(body, "Criteria"),
            "scope": get_section(body, "Scope"),
            "verify": get_section(body, "Verify"),
            "decisions": get_section(body, "Decisions"),
            "depends": get_section(body, "Depends"),
            "log": log_entries(body)}


EDITABLE = {"title", "team", "status", "blocked", "ref", "description", "criteria",
            "scope", "verify", "decisions", "depends"}
SECTIONS = {"description", "criteria", "scope", "verify", "decisions", "depends"}
TRANSITIONS = {"backlog": {"todo"}, "todo": {"backlog", "doing"},
               "doing": {"todo", "qa"}, "qa": {"doing", "done"}, "done": {"todo"}}
MESSAGE = re.compile(r"^(TASK|DONE|BLOCKED|ASK|ANSWER|CONTRACT|STATUS) (-|T[0-9]+(?:,T[0-9]+)*) \| (.+)$")


def _manager(actor, primary):
    if actor not in ("human", primary):
        raise ValueError("only the human or primary team may change a ticket")


def _note(body, text):
    return set_section(body, "Log", (get_section(body, "Log") +
                       f"\n- {now()} {_clean(text)}").strip())


def _save(shared, meta, body):
    meta["updated"] = now()
    _atomic_write(path_of(shared, meta["id"]), serialize(meta, body))
    return to_dict(meta, body)


def _changes(meta, body, changes, actor, primary, teams=None):
    _manager(actor, primary)
    unknown = set(changes) - EDITABLE
    if unknown:
        raise ValueError(f"unknown fields: {sorted(unknown)}")
    if "team" in changes and teams is not None and changes["team"] not in {*teams, "-"}:
        raise ValueError(f"unknown team {changes['team']!r} (expected one of {', '.join(teams)} or -)")
    target = changes.get("status", meta["status"])
    if target != meta["status"] and target not in TRANSITIONS[meta["status"]]:
        raise ValueError(f"invalid transition {meta['status']} -> {target}")
    previous = dict(meta)
    for key, value in changes.items():
        if key in SECTIONS:
            body = set_section(body, key.capitalize(), str(value))
        elif key == "blocked":
            meta[key] = value if isinstance(value, bool) else str(value).lower() == "true"
        else:
            meta[key] = _clean(value)
    events = [f'{key} {previous.get(key)} → {meta.get(key)}' for key in ('status', 'team', 'blocked')
              if previous.get(key) != meta.get(key)]
    return meta, _note(body, f"{actor}: {'; '.join(events)}") if events else body


def create(shared: Path, title: str, *, team="-", status="backlog", ref="",
           description="", criteria="", by="human", primary="manager", teams=None, **mandate) -> dict:
    _manager(by, primary)
    if status not in ("backlog", "todo"):
        raise ValueError("new tickets start in backlog or todo")
    if teams is not None and team not in {*teams, "-"}:
        raise ValueError(f"unknown team {team!r} (expected one of {', '.join(teams)} or -)")
    with lock(shared):
        tid = alloc_id(shared)
        meta = {"id": tid, "title": _clean(title) or "(untitled)", "team": team,
                "status": status, "blocked": False, "ref": ref, "created": now(), "by": by}
        body = ""
        for key, value in {"description": description, "criteria": criteria, **mandate}.items():
            if key not in SECTIONS:
                raise ValueError(f"unknown mandate field {key}")
            body = set_section(body, key.capitalize(), str(value))
        return _save(shared, meta, _note(body, f"created by {by} ({status})"))


def update(shared, tid, changes, *, actor="human", primary="manager", teams=None):
    with lock(shared):
        meta, body = parse(path_of(shared, tid))
        previous = serialize(meta, body)
        meta, body = _changes(meta, body, changes, actor, primary, teams)
        if serialize(meta, body) == previous:
            return to_dict(meta, body)
        return _save(shared, meta, body)





def append_log(shared, tid, text, *, actor="human", primary="manager"):
    with lock(shared):
        meta, body = parse(path_of(shared, tid))
        if actor not in ("human", primary, meta["team"]):
            raise ValueError("notes require the owner, primary team or human")
        return _save(shared, meta, _note(body, text))


def delete(shared, tid, *, actor="human"):
    if actor != "human":
        raise ValueError("only the human may delete a ticket")
    with lock(shared):
        path_of(shared, tid).unlink(missing_ok=True)


def message_parts(header):
    match = MESSAGE.fullmatch(header.strip())
    if not match:
        raise ValueError("expected TYPE T1[,T2] | summary (or - instead of ticket ids)")
    typ, refs, _ = match.groups()
    return typ, [] if refs == "-" else list(dict.fromkeys(refs.split(",")))


def canonical_team(name, teams, prefix=""):
    if name in teams:
        return name
    candidate = name[len(prefix) + 1:] if prefix and name.startswith(prefix + "-") else name
    if candidate not in teams:
        raise ValueError(f"unknown team recipient {name!r}")
    return candidate


def _message_records(shared, sender, to, header, primary, event_id):
    typ, ids = message_parts(header)
    marker = f"<!-- event:{event_id} -->" if event_id else ""
    if event_id and not re.fullmatch(r"[a-zA-Z0-9_.:-]+", event_id):
        raise ValueError("invalid event id")
    records = []
    for tid in ids:
        meta, body = parse(path_of(shared, tid))
        if marker and marker in body:
            continue
        if typ == "TASK":
            if sender != primary or to == primary:
                raise ValueError("TASK must be sent by the primary team to an execution team")
            if meta["status"] not in ("todo", "doing") or meta["team"] not in ("-", to):
                raise ValueError(f"{tid} is not ready for {to}; backlog is human-owned")
            if not get_section(body, "Criteria").strip():
                raise ValueError(f"{tid} needs acceptance criteria before dispatch")
            meta.update(status="doing", team=to, blocked=False)
        elif typ in ("DONE", "BLOCKED"):
            if to != primary or sender != meta["team"]:
                raise ValueError(f"{typ} must come from {tid}'s owner to the primary team")
            if meta["status"] not in ("doing", "qa"):
                raise ValueError(f"{tid} is not active")
            meta["blocked"] = typ == "BLOCKED"
            if typ == "DONE":
                meta["status"] = "qa"
        body = _note(body, f"{sender} → {to} | {header.strip()}")
        if marker:
            body += "\n" + marker + "\n"
        records.append((meta, body))
    return records


def apply_message(shared, sender, to, header, *, primary="manager", event_id=None, validate_only=False):
    """Only the reference field changes tickets. Successful tool events are replay-safe."""
    with lock(shared):
        records = _message_records(shared, sender, to, header, primary, event_id)
        if not validate_only:
            for meta, body in records:
                _save(shared, meta, body)
        return [meta["id"] for meta, _ in records]


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
            + (f"  ({t['ref']})" if t["ref"] else "")
            for t in ts if t["status"] != "done"]
    return head + ("\n  " + "\n  ".join(rows) if rows else "")
