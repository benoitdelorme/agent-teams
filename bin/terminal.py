"""Terminal drivers: where team sessions live and how typed text reaches them.

The launcher and the board only see a *driver* and opaque *handles*:

    drv = detect(cfg, root)              # programa inside programa, else tmux if installed, else manual
    h = drv.open("backend", "Backend", cwd, purpose)   # one terminal per team
    drv.wait_ready(h); drv.send(h, "claude ...\\n")
    drv.tty(h) / drv.exists(h) / drv.select(h) / drv.close(h)

`.state/terminal.json` records the driver name and one handle per team, so later commands
(status, msg, down, the board) talk to the same terminals.  A driver never exits the
process: it returns False / None on failure and the caller decides.
"""
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

NAMES = ("programa", "tmux", "manual")


def in_programa() -> bool:
    return bool(os.environ.get("PROGRAMA_SURFACE_ID") and os.environ.get("PROGRAMA_SOCKET_PATH"))


def _run(args, timeout=10, input=None):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, input=input)
    except (OSError, subprocess.TimeoutExpired):
        return None


class Driver:
    """Interface. `board_in_terminal`: the board server is started in an extra tab/window next
    to the primary team (needed by programa, whose `send` refuses orphan clients; convenient in
    tmux for the logs). `manual` starts it detached instead."""
    name = "manual"
    board_in_terminal = False

    def __init__(self, cfg: dict, root: Path):
        self.cfg, self.root = cfg, Path(root)
        self.prompt_re = cfg.get("shell_prompt_regex", r"(➜|→|❯|\$|%|#) ")

    def available(self) -> bool:
        return True

    def open(self, name: str, title: str, cwd: Path, purpose: str = "") -> dict | None:
        return None

    def open_tab(self, near: dict | None, title: str, cwd: Path) -> dict | None:
        return None

    def exists(self, handle: dict) -> bool:
        return False

    def wait_ready(self, handle: dict, timeout: float = 15):
        pass

    def send(self, handle: dict, text: str) -> bool:
        return False

    def tty(self, handle: dict) -> str | None:
        return None

    def select(self, handle: dict):
        pass

    def close(self, handle: dict):
        pass

    def describe(self, handle: dict) -> str:
        return "-"

    def attach_hint(self) -> str:
        return ""


class Manual(Driver):
    """No terminal multiplexer: `teams up` prints the commands to run yourself."""
    name = "manual"


class Programa(Driver):
    """programa: one workspace per team; the board is a tab in the primary team's pane."""
    name = "programa"
    board_in_terminal = True

    def __init__(self, cfg, root):
        super().__init__(cfg, root)
        self._tree_cache = {}

    def available(self) -> bool:
        return in_programa()

    def _cmd(self, *args, timeout=10) -> str | None:
        r = _run(["programa", *args], timeout=timeout)
        return r.stdout.strip() if r and r.returncode == 0 else None

    def _tree(self, ws: str) -> dict:
        import json
        if ws not in self._tree_cache:
            out = self._cmd("--json", "tree", "--workspace", ws)
            try:
                self._tree_cache[ws] = json.loads(out) if out else {}
            except json.JSONDecodeError:
                self._tree_cache[ws] = {}
        return self._tree_cache[ws]

    def _surfaces(self, ws: str):
        for w in self._tree(ws).get("windows", []):
            for x in w.get("workspaces", []):
                if x.get("ref") != ws:
                    continue
                for pane in x.get("panes", []):
                    for sf in pane.get("surfaces", []):
                        yield pane, sf

    def open(self, name, title, cwd, purpose=""):
        args = ["new-workspace", "--name", title, "--cwd", str(cwd)]
        if purpose:
            args += ["--description", purpose]
        out = self._cmd(*args)                                   # "OK workspace:6"
        if not out or len(out.split()) < 2:
            return None
        ws = out.split()[1]
        self._tree_cache.pop(ws, None)
        surf = next((sf["ref"] for _, sf in self._surfaces(ws) if sf.get("type") == "terminal"), None)
        return {"workspace": ws, "surface": surf} if surf else None

    def open_tab(self, near, title, cwd):
        args = ["new-surface"]
        if near:
            pane = next((p.get("ref") for p, sf in self._surfaces(near["workspace"]) if sf.get("ref") == near["surface"]), None)
            if pane:
                args += ["--workspace", near["workspace"], "--pane", pane]
        out = self._cmd(*args)                                   # "OK surface:55 pane:27 workspace:36"
        if not out:
            return None
        surf = next((p for p in out.split() if p.startswith("surface:")), None)
        ws = next((p for p in out.split() if p.startswith("workspace:")),
                  (near or {}).get("workspace") or os.environ.get("PROGRAMA_WORKSPACE_ID", ""))
        if not surf:
            return None
        self._cmd("rename-tab", "--workspace", ws, "--surface", surf, title)
        return {"workspace": ws, "surface": surf}

    def exists(self, handle):
        self._tree_cache.pop(handle["workspace"], None)
        return any(sf.get("ref") == handle["surface"] for _, sf in self._surfaces(handle["workspace"]))

    def wait_ready(self, handle, timeout=15):
        r = _run(["programa", "wait-surface", "--workspace", handle["workspace"], "--surface", handle["surface"],
                  "--pattern", self.prompt_re, "--timeout", str(int(timeout))], timeout=timeout + 5)
        if not r or r.returncode != 0:
            time.sleep(3)                                        # give the shell a moment anyway
        time.sleep(0.3)

    def send(self, handle, text):
        r = _run(["programa", "send", "--workspace", handle["workspace"], "--surface", handle["surface"], text], timeout=5)
        return bool(r and r.returncode == 0)

    def tty(self, handle):
        if not self.available():
            return None
        return next((sf.get("tty") for _, sf in self._surfaces(handle["workspace"]) if sf.get("ref") == handle["surface"]), None)

    def select(self, handle):
        self._cmd("select-workspace", "--workspace", handle["workspace"])

    def close(self, handle):
        self._cmd("close-workspace", "--workspace", handle["workspace"])

    def describe(self, handle):
        return f"{handle['workspace']} / {handle['surface']}"


class Tmux(Driver):
    """tmux: one detached session per instance (`teams-<project>`), one window per team."""
    name = "tmux"
    board_in_terminal = True

    def __init__(self, cfg, root):
        super().__init__(cfg, root)
        project = self.root.parent if self.root.name in (".teams", "teams") else self.root
        slug = re.sub(r"[^a-z0-9-]+", "-", project.name.lower()).strip("-") or "project"
        self.session = cfg.get("tmux_session") or f"teams-{slug}"

    def available(self) -> bool:
        return shutil.which("tmux") is not None

    def _cmd(self, *args, timeout=10) -> str | None:
        r = _run(["tmux", *args], timeout=timeout)
        return r.stdout.strip() if r and r.returncode == 0 else None

    def _session_exists(self) -> bool:
        return self._cmd("has-session", "-t", f"={self.session}") is not None     # `=`: exact name, not a prefix

    def _window(self, title, cwd) -> dict | None:
        if self._session_exists():
            out = self._cmd("new-window", "-d", "-t", f"={self.session}:", "-n", title, "-c", str(cwd), "-P", "-F", "#{window_id}")
        else:
            out = self._cmd("new-session", "-d", "-s", self.session, "-n", title, "-c", str(cwd), "-P", "-F", "#{window_id}")
        return {"session": self.session, "window": out} if out else None

    def open(self, name, title, cwd, purpose=""):
        return self._window(title, cwd)

    def open_tab(self, near, title, cwd):
        return self._window(title, cwd)

    def exists(self, handle):
        out = self._cmd("list-windows", "-a", "-F", "#{window_id}") or ""
        return handle["window"] in out.split()

    def wait_ready(self, handle, timeout=15):
        pat = re.compile(self.prompt_re)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            out = self._cmd("capture-pane", "-p", "-t", handle["window"]) or ""
            last = next((l for l in reversed(out.splitlines()) if l.strip()), "")
            if pat.search(last + " "):                       # capture-pane strips trailing spaces; the prompt regex expects one
                time.sleep(0.3)
                return
            time.sleep(0.2)

    def send(self, handle, text):
        r = _run(["tmux", "send-keys", "-t", handle["window"], "-l", "--", text.rstrip("\n")], timeout=5)
        if not r or r.returncode != 0:
            return False
        r = _run(["tmux", "send-keys", "-t", handle["window"], "Enter"], timeout=5)
        return bool(r and r.returncode == 0)

    def tty(self, handle):
        return self._cmd("display-message", "-p", "-t", handle["window"], "#{pane_tty}") or None

    def select(self, handle):
        self._cmd("select-window", "-t", handle["window"])

    def close(self, handle):
        self._cmd("kill-window", "-t", handle["window"])

    def describe(self, handle):
        return f"{handle['session']}:{handle['window']}"

    def attach_hint(self):
        return "" if os.environ.get("TMUX") else f"attach with: tmux attach -t {self.session}"


DRIVERS = {"programa": Programa, "tmux": Tmux, "manual": Manual}


def driver(name: str, cfg: dict, root: Path) -> Driver:
    if name not in DRIVERS:
        raise ValueError(f"unknown terminal driver {name!r} (expected one of {', '.join(NAMES)})")
    return DRIVERS[name](cfg, root)


def detect(cfg: dict, root: Path) -> Driver:
    """`terminal` in teams.json: programa | tmux | manual | auto (default).
    auto = programa when running inside programa, else tmux when installed, else manual."""
    want = cfg.get("terminal", "auto")
    if want != "auto":
        return driver(want, cfg, root)
    for name in ("programa", "tmux"):
        d = driver(name, cfg, root)
        if d.available():
            return d
    return Manual(cfg, root)
