"""Remote instances: the teams run on another machine, this one drives them over ssh and shows them.

    teams link sky-a:~/work/project      # writes ./.teams/remote.json: commands run from here drive that instance
    teams up                             # `teams up` over there (tmux), then one local view per team
    teams attach                         # open the missing views again: a reboot, a closed window, a lost network
    teams down                           # `teams down` over there, then close the views and the board tunnel
    teams status / task / msg / cost …   # relayed over ssh as they are

The target is `--remote host:path`, else `$TEAMS_REMOTE`, else the nearest `.teams/remote.json`
or `teams/remote.json` walking up from the cwd (a `teams.json` found nearer keeps the instance
local). `init` and `link` only go remote with `--remote`; agents on the server have `TEAMS_CONFIG`
set and never go remote. A command with a target runs over there as `teams <same arguments>`,
inside the project, through the remote user's login shell so its PATH finds teams and claude.
Every word reaches a shell between single quotes: none is left bare for it to expand.

The teams live in tmux on the server, so they survive this machine sleeping or losing the network.
A view is a terminal of the local driver (a programa workspace, a tmux window, or a command printed
for you) in which a `sh -c` loop runs `ssh -t host`, then, through the login shell over there,
`tmux new-session -A -s <session>-<team> -t =<session>`: a session grouped with the teams' one, so
each view shows its own team whatever the others show, with the tmux the teams were started with.
The loop reconnects when ssh exits 255 (connection failed or lost) and ends on any other code. The
board listens on the server's 127.0.0.1; the same kind of loop, in the background, forwards it to
the same port here. What this machine opened is recorded in `.state/views.json` beside remote.json
(under ~/.local/state/teams/ for a target given by flag or environment).

remote.json: {"host": "sky-a", "path": "~/work/project"}, optionally "command" (default "teams"),
"ssh_options" (a list of ssh arguments), "terminal" (the local driver, as in teams.json) and
"mouse" (false: no tmux mouse mode in the views). It belongs to one machine: keep it out of git.
"""
import json
import os
import re
import signal
import socket
import subprocess
import sys
from pathlib import Path

import terminal

CANDIDATES = (".teams/remote.json", "teams/remote.json")
_VERSION = Path(__file__).resolve().parent.parent / "VERSION"
ENGINE_VERSION = _VERSION.read_text().strip() if _VERSION.is_file() else "0"       # as bin/teams reads it
KEEPALIVE = ("-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3")       # a dead connection is noticed within ~45 s
RETRY = 3                                                                          # seconds before ssh is run again after a 255


class RemoteError(OSError):
    """The server could not be reached, or did not answer as expected."""


def parse_target(spec: str) -> dict:
    host, sep, path = spec.partition(":")
    if not sep or not host or not path:
        raise ValueError(f"remote target must be host:path, got {spec!r}")
    return {"host": host, "path": path}


def find(cwd: Path, local_candidates) -> dict | None:
    """$TEAMS_REMOTE, else the nearest remote.json walking up; None when a local teams.json is nearer."""
    if os.environ.get("TEAMS_REMOTE"):
        return parse_target(os.environ["TEAMS_REMOTE"])
    for base in [cwd, *cwd.parents]:
        for rel in CANDIDATES:
            f = base / rel
            if f.is_file():
                target = json.loads(f.read_text())
                if not target.get("host") or not target.get("path"):
                    raise ValueError(f"{f}: needs \"host\" and \"path\"")
                return {**target, "_file": f}
        if any((base / rel).is_file() for rel in local_candidates):
            return None
    return None


def quote(word: str) -> str:
    """A word as the server's shell must read it: always between single quotes, never bare.
    A bare word is the shell's to expand, and which words it expands depends on the shell: zsh
    turns `=ls` into `/bin/ls`, which `shlex.quote` leaves bare."""
    return "'" + word.replace("'", "'\"'\"'") + "'"


def _remote_path(path: str) -> str:
    """The project path for the server's shell, leaving a leading ~ outside the quotes for it to expand."""
    if path == "~" or path.startswith("~/"):
        rest = path[2:]
        return "~/" + quote(rest) if rest else "~"
    return quote("./" + path if path.startswith("-") else path)    # never an option of cd


def remote_line(target: dict, argv: list) -> str:
    """`teams <argv>` in the project, through a login shell so the server's PATH finds teams and claude."""
    inner = f"cd {_remote_path(target['path'])} && {target.get('command', 'teams')} {' '.join(quote(x) for x in argv)}"
    return f'exec "$SHELL" -lc {quote(inner)}'


def ssh_argv(target: dict, line: str | None = None, tty: bool = False, options=()) -> list:
    return ["ssh", *(["-t"] if tty else []), *options, *target.get("ssh_options", []), target["host"],
            *([line] if line else [])]


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def run(target: dict, argv: list) -> int:
    """`teams <argv>` on the server, its output streamed here; its exit code."""
    try:
        return subprocess.call(ssh_argv(target, remote_line(target, argv)))
    except OSError as exc:
        raise RemoteError(f"ssh {target['host']}: {exc}")


def relay(target: dict, argv: list):
    """Hand this process over to ssh: exit code, signals and terminal behave as if the command ran here."""
    os.execvp("ssh", ssh_argv(target, remote_line(target, argv), tty=_interactive()))


def status(target: dict) -> dict:
    """`teams status --json` on the server (its last JSON line: a login shell may print before it)."""
    try:
        r = subprocess.run(ssh_argv(target, remote_line(target, ["status", "--json"])),
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RemoteError(f"ssh {target['host']}: {exc}")
    line = next((l for l in reversed(r.stdout.split("\n")) if l.startswith("{")), None)
    if r.returncode != 0 or not line:
        why = (r.stderr.strip().splitlines() or [f"exit {r.returncode}, no JSON on stdout"])[-1]
        if "--json" in why:
            why += " (the engine over there predates remote instances: update it with git pull)"
        raise RemoteError(f"{target['host']}:{target['path']}: {why}")
    return json.loads(line)


def link(spec: str, inst_dir: str) -> int:
    """Point a local directory at a remote instance, once the server has answered."""
    target = parse_target(spec)
    st = status(target)
    f = Path(inst_dir).resolve() / "remote.json"
    try:
        old = json.loads(f.read_text())
        previous = f"{old.get('host')}:{old.get('path')}"
    except (OSError, json.JSONDecodeError):
        previous = None
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(target, indent=2) + "\n")
    names = ", ".join(t["name"] for t in st.get("teams", []))
    print(f"linked {f} → {spec}" + (f" (was {previous})" if previous and previous != spec else ""))
    print(f"  teams: {names or '(none)'} — {'up' if st.get('up') else 'down'}, engine {st.get('engine', '?')}")
    print(f"next: `teams up` from anywhere under {f.parent.parent}")
    return 0


# ---------- views: one local terminal per team, attached over ssh ----------------
def _join(words) -> str:
    """The words as one line for a shell, each through `quote`."""
    return " ".join(quote(w) for w in words)


def _loop(command: str, what: str) -> str:
    """A POSIX loop running `command` again each time it exits 255 (ssh: connection failed or lost);
    any other code (a detach, the session gone, the teams stopped) ends the loop with that code."""
    lost = quote(f"{what}: connection lost, retrying in {RETRY} s")
    return f'while :; do {command}; code=$?; [ "$code" -eq 255 ] || exit "$code"; echo {lost}; sleep {RETRY}; done'


def view_line(target: dict, session: str, window: str, team: str, mouse: bool = True) -> str:
    """The line typed into a view's terminal: attach a tmux session grouped with the teams' one, on this
    team's window, and reconnect by itself. `sh -c` keeps it POSIX whatever shell the terminal runs.
    Over there it goes through the login shell, as `remote_line` does, so it finds the tmux the teams
    were started with; a terminal type the server has no terminfo for (xterm-ghostty…) falls back to
    xterm-256color. Every word is quoted at every level: zsh reads a bare `=<session>` as a command."""
    view = f"{session}-{team}"
    tmux = ["tmux", "new-session", "-A", "-s", view, "-t", f"={session}", ";", "select-window", "-t", f"{view}:{window}"]
    if mouse:                                    # the wheel scrolls tmux's history instead of the prompt's
        tmux += [";", "set-option", "-t", view, "mouse", "on"]
    inner = 'infocmp "$TERM" >/dev/null 2>&1 || export TERM=xterm-256color; exec ' + _join(tmux)
    on_server = f'exec "$SHELL" -lc {quote(inner)}'
    return "sh -c " + quote(_loop(_join(ssh_argv(target, on_server, tty=True, options=KEEPALIVE)), view))


def view_alive(drv, handle: dict, marker: str) -> bool:
    """A process on the view's terminal names its view session: the loop, or the ssh it runs.
    True when that cannot be read (no tty, ps failing): a terminal is never typed into on a guess."""
    tty = drv.tty(handle)
    if not tty:
        return True
    try:
        r = subprocess.run(["ps", "-ww", "-t", tty.removeprefix("/dev/"), "-o", "command="],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return True
    if r.returncode != 0 or not r.stdout.strip():
        return True
    return re.search(rf"(?<![\w-]){re.escape(marker)}(?![\w-])", r.stdout) is not None     # teams-p-web is not teams-p-web-admin


def state_file(target: dict) -> Path:
    """Where this machine records the views of a target: beside remote.json, or under
    ~/.local/state/teams for a target given by --remote or $TEAMS_REMOTE."""
    if target.get("_file"):
        return target["_file"].parent / ".state" / "views.json"
    slug = re.sub(r"[^a-z0-9]+", "-", f"{target['host']}-{target['path']}".lower()).strip("-")
    return Path.home() / ".local" / "state" / "teams" / slug / "views.json"


def _read(f: Path) -> dict:
    try:
        return json.loads(f.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write(f: Path, data: dict):
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2))


def local_driver(target: dict, views: dict | None = None) -> terminal.Driver:
    """The driver the recorded views were opened with, else the one remote.json asks for or the detected one."""
    cfg = {k: v for k, v in target.items() if not k.startswith("_")}
    root = state_file(target).parent.parent
    if views and views.get("driver"):
        return terminal.driver(views["driver"], cfg, root)
    return terminal.detect(cfg, root)


# ---------- the board, forwarded to the same port here ---------------------------
def board_port(url: str | None) -> int | None:
    m = re.match(r"https?://[^/]+:(\d+)", url or "")
    return int(m.group(1)) if m else None


def port_free(port: int) -> bool:
    """Nothing is bound to 127.0.0.1:<port> here — asked as ssh will ask, with SO_REUSEADDR."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def open_tunnel(target: dict, port: int, log: Path) -> int | None:
    """Forward the server's 127.0.0.1:<port> to the same port here, with a reconnecting loop in the
    background; its pid, which is also its process group. None when the port is busy here: `ssh -N`
    exits 255 on a failed forward too, so the loop would spin."""
    if not port_free(port):
        return None
    ssh = ssh_argv(target, options=["-N", "-o", "ExitOnForwardFailure=yes", *KEEPALIVE, "-L", f"{port}:127.0.0.1:{port}"])
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(log, "ab") as fh:
            p = subprocess.Popen(["sh", "-c", _loop(_join(ssh), f"board tunnel {port}")],
                                 stdin=subprocess.DEVNULL, stdout=fh, stderr=fh, start_new_session=True)
    except OSError:
        return None
    return p.pid


def _tunnel_alive(tunnel: dict) -> bool:
    """The recorded pid still runs the forward of the recorded port. A pid alone proves nothing:
    after a reboot it belongs to another program, which `close_tunnel` must not signal."""
    pid, port = tunnel.get("pid"), tunnel.get("port")
    if not pid or not port:
        return False
    try:
        r = subprocess.run(["ps", "-ww", "-p", str(pid), "-o", "command="], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return quote(f"{port}:127.0.0.1:{port}") in r.stdout          # the forward as the loop wrote it


def close_tunnel(views: dict):
    """SIGTERM to the recorded tunnel's whole process group: the loop, its ssh, its sleep."""
    tunnel = views.get("tunnel") or {}
    if _tunnel_alive(tunnel):
        try:
            os.killpg(tunnel["pid"], signal.SIGTERM)
        except OSError:
            pass


# ---------- up / attach / down: the teams over there, their views here ------------
def _close(target: dict, views: dict):
    """Close what a views state records: every view still there, then the board tunnel."""
    drv = local_driver(target, views)
    for name, h in views.get("handles", {}).items():
        if drv.exists(h):
            drv.close(h)
            print(f"[{name}] view closed {drv.describe(h)}")
    close_tunnel(views)


def _open_views(target: dict, st: dict, drv, handles: dict):
    """One view per team, the primary's last so it ends up in front: open the missing ones, type the
    line again where the terminal is still there but its view is gone, leave the live ones alone."""
    host, where = target["host"], f"{target['host']}:{target['path']}"
    teams = st.get("teams", [])
    if drv.name == "manual":
        print("No programa or tmux here — run these yourself, one per terminal:\n")
    for t in [t for t in teams if not t.get("primary")] + [t for t in teams if t.get("primary")]:
        name, there = t["name"], t.get("handle") or {}
        if not there.get("window"):
            print(f"[{name}] no terminal over there — `teams up --resume` recreates it")
            continue
        view = f"{there['session']}-{name}"
        line = view_line(target, there["session"], there["window"], name, target.get("mouse", True))
        if drv.name == "manual":
            print(f"# {name}\n{line}\n")
            continue
        h = handles.get(name)
        if h and drv.exists(h):
            if view_alive(drv, h, view):
                print(f"[{name}] view already open {drv.describe(h)}")
                continue
            verb = "reconnected"                 # the terminal is still there, its ssh is gone
        else:
            h = drv.open(name, t.get("title", name), Path.cwd(), f"{t.get('purpose', '')} (on {where})".strip())
            if not h:
                raise RemoteError(f"{drv.name}: could not open a view for {name}")
            handles[name] = h
            drv.wait_ready(h)
            verb = "opened"
        if not drv.send(h, line + "\n"):
            raise RemoteError(f"{drv.name}: could not type into {name}'s view")
        print(f"[{name}] view {verb} {drv.describe(h)} → {host}")


def _forward_board(target: dict, st: dict, tunnel: dict, log: Path) -> dict:
    """The tunnel to record: the recorded one while it forwards the board's port, else a new one, else none."""
    host, port = target["host"], board_port(st.get("board"))
    if port and tunnel.get("port") == port and _tunnel_alive(tunnel):
        print(f"board → http://127.0.0.1:{port}  (forwarded from {host}, already running)")
        return tunnel
    close_tunnel({"tunnel": tunnel})
    if not port:
        return {}
    pid = open_tunnel(target, port, log)
    if not pid:
        by_hand = _join(ssh_argv(target, options=["-N", "-L", f"{port}:127.0.0.1:{port}"]))
        print(f"board: port {port} is busy here, not forwarded — free it then `teams attach`, or by hand "
              f"(change the first {port} for another local port): {by_hand}")
        return {}
    print(f"board → http://127.0.0.1:{port}  (forwarded from {host})")
    return {"pid": pid, "port": port}


def attach(target: dict, st: dict) -> int:
    """Open a local view for every team that lacks one, forward the board, select the primary's view."""
    host = target["host"]
    if not st.get("up"):
        raise RemoteError(f"the teams are down on {host} — `teams up` starts them")
    if st.get("driver") != "tmux":
        raise RemoteError(f"the teams on {host} run with the {st.get('driver')!r} driver; a remote instance needs "
                          f"\"terminal\": \"tmux\" in its teams.json (then `teams down` and `teams up`)")
    if st.get("engine") != ENGINE_VERSION:
        print(f"teams: engine {st.get('engine', '?')} on {host}, {ENGINE_VERSION} here — bring both to the same version",
              file=sys.stderr)
    sf = state_file(target)
    views = _read(sf)
    if views and views.get("started_at") != st.get("started_at"):    # another run over there: these views show closed windows
        _close(target, views)
        views = {}
    drv = local_driver(target, views)
    views = {"driver": drv.name, "handles": views.get("handles", {}), "started_at": st.get("started_at"),
             "tunnel": views.get("tunnel") or {}, "target": f"{host}:{target['path']}"}
    try:
        _open_views(target, st, drv, views["handles"])
        views["tunnel"] = _forward_board(target, st, views["tunnel"], sf.parent / "tunnel.log")
    finally:
        _write(sf, views)                        # whatever was opened is recorded: `teams down` can close it
    primary = next((t["name"] for t in st.get("teams", []) if t.get("primary")), None)
    if primary in views["handles"]:
        drv.select(views["handles"][primary])
        hint = drv.attach_hint()
        print(f"\n{primary} is selected - talk to it there. `teams down` stops the teams on {host}."
              + (f"\n{hint}" if hint else ""))
    return 0


def up(target: dict, resume: bool) -> int:
    """`teams up` over there, then the views. The server refuses a second `up`: say first that `teams attach` is the way."""
    st = status(target)
    if st.get("up") and not resume:
        raise RemoteError(f"teams already up on {target['host']} — `teams attach` opens the views, `teams down` stops them")
    code = run(target, ["up", "--resume"] if resume else ["up"])
    return code or attach(target, status(target))


def down(target: dict) -> int:
    """`teams down` over there first: each view's tmux ends and its loop stops by itself. Then close what is left here."""
    code = run(target, ["down"])
    sf = state_file(target)
    _close(target, _read(sf))
    sf.unlink(missing_ok=True)
    return code


def strip_option(argv: list, name: str) -> list:
    """argv without `name value` / `name=value`: the server finds its own instance.

    Only the options ahead of the command are read: from the command (or a `--`) on, the words are
    the command's own and travel untouched. `name` must be spelled in full, which the launcher's
    parser enforces by refusing abbreviations.
    """
    out, i = [], 0
    while i < len(argv) and argv[i].startswith("-") and argv[i] != "--":
        if argv[i] == name:
            i += 2
            continue
        if not argv[i].startswith(name + "="):
            out.append(argv[i])
        i += 1
    return out + argv[i:]


def main(target: dict, a, argv: list):
    """Run a command whose instance lives on another machine; up, attach and down also manage the views here."""
    if a.cmd == "up" and not a.dry_run:
        return up(target, a.resume)
    if a.cmd == "attach":
        return attach(target, status(target))
    if a.cmd == "down":
        return down(target)
    relay(target, argv)
