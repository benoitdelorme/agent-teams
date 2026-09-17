"""Terminal drivers: where team sessions live and how typed text reaches them.

The launcher and the board only see a *driver* and opaque *handles*:

    drv = detect(cfg, root)              # programa inside programa, else tmux, else warp inside Warp, else manual
    h = drv.open("backend", "Backend", cwd, purpose, command)   # one terminal per team
    drv.wait_ready(h); drv.send(h, "claude ...\\n")              # `send` only when drv.types_commands
    drv.tty(h) / drv.exists(h) / drv.select(h) / drv.close(h)

`.state/terminal.json` records the driver name and one handle per team, so later commands
(status, msg, down, the board) talk to the same terminals.  A driver never exits the
process: it returns False / None on failure and the caller decides.

Two families: drivers that can type into a terminal they opened (programa, tmux) and drivers
that cannot (warp — no scripting API).  The second kind is handed the command to run when the
terminal is opened, which is why `open` takes one.

A multiplexer also hides its sessions from the terminal hosting it: the tmux driver prepares each
session it creates so a lead's status can still get out (see `Tmux._prepare_session` and
bin/hostterm.py).
"""
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import hostterm

NAMES = ("programa", "tmux", "warp", "manual")

SELF = Path(__file__).resolve().parent / "teams"    # the CLI next to this module, for what a terminal runs itself
WARP_TABS = Path.home() / ".warp" / "tab_configs"   # Warp reads one .toml per tab config from here
WARP_COLOR = "blue"                                 # same colour on every team tab (Warp cannot group tabs from a file)


def in_programa() -> bool:
    return bool(os.environ.get("PROGRAMA_SURFACE_ID") and os.environ.get("PROGRAMA_SOCKET_PATH"))


def _run(args, timeout=10, input=None):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, input=input)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _ps(pid: int, fmt: str) -> str:
    """One `ps` field of one process, empty when it is gone."""
    r = _run(["ps", "-o", fmt, "-p", str(pid)], timeout=5)
    return r.stdout.strip() if r and r.returncode == 0 else ""


def project_slug(root: Path) -> str:
    """Project name for a session or tab name: the directory HOLDING the instance, sanitised."""
    root = Path(root)
    project = root.parent if root.name in (".teams", "teams") else root
    return re.sub(r"[^a-z0-9-]+", "-", project.name.lower()).strip("-") or "project"


# ---------- recorded runs ----------------------------------------------------
# A terminal that cannot be typed into is handed its command when it opens, so the launcher never
# learns a pid from the terminal itself. `teams _run` records one here before becoming the lead;
# any such driver reads it back. Nothing below is specific to one driver.

def pid_file(root: Path, name: str) -> Path:
    """Line 1: the runner pid (the lead after the exec). Line 2: the terminal's shell + its start time."""
    return Path(root) / ".state" / "runs" / f"{name}.pid"


def record_run(root: Path, name: str):
    """Called by `teams _run` just before it execs the lead: this process IS the session from now on."""
    f = pid_file(root, name)
    f.parent.mkdir(parents=True, exist_ok=True)
    ppid = os.getppid()
    f.write_text(f"{os.getpid()}\n{ppid} {_ps(ppid, 'lstart=')}\n")


def run_pid(root: Path, name: str) -> int | None:
    try:
        return int(pid_file(root, name).read_text().splitlines()[0])
    except (OSError, ValueError, IndexError):
        return None


def run_shell_pid(root: Path, name: str) -> int | None:
    """The terminal's shell, only if that exact process is still there (pid reuse guard)."""
    try:
        line = pid_file(root, name).read_text().splitlines()[1]
    except (OSError, IndexError):
        return None
    pid, _, started = line.partition(" ")
    return int(pid) if pid.isdigit() and started and _ps(int(pid), "lstart=") == started else None


class Driver:
    """Interface. `board_in_terminal`: the board server is started in an extra tab/window next
    to the primary team (needed by programa, whose `send` refuses orphan clients; convenient in
    tmux for the logs). `manual` starts it detached instead. `types_commands`: the driver can
    type text into a terminal after opening it — when it cannot, `open` must be given the
    command to run and `msg` / board wake-ups have nowhere to go."""
    name = "manual"
    board_in_terminal = False
    types_commands = True

    def __init__(self, cfg: dict, root: Path):
        self.cfg, self.root = cfg, Path(root)
        self.prompt_re = cfg.get("shell_prompt_regex", r"(➜|→|❯|\$|%|#) ")

    def available(self) -> bool:
        return True

    def open(self, name: str, title: str, cwd: Path, purpose: str = "", command: str | None = None) -> dict | None:
        """`command` is the shell line to run in the new terminal; drivers that type it later ignore it."""
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
        """What `teams up` adds about this terminal once every team is started. Empty: nothing to say."""
        return ""

    def show(self, text: str):
        """Keep one line of instance status visible in the terminal (the board URL): drivers with a
        status bar display it, the others have nowhere to put it."""
        pass

    def title(self, text: str):
        """Name the terminal hosting the whole instance after `text` (the primary team), where the
        driver can: a multiplexer sets the title of the terminal it is attached in, which is otherwise
        named after the command that attached it."""
        pass


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

    def open(self, name, title, cwd, purpose="", command=None):
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


HOST_TERMINAL_ENV = ("TERM_PROGRAM", "TERM_PROGRAM_VERSION",       # who is hosting the session, copied into
                     "WARP_CLI_AGENT_PROTOCOL_VERSION", "WARP_CLIENT_VERSION")   # it under hostterm.HOST_ENV_PREFIX


class Tmux(Driver):
    """tmux: one detached session per instance (`teams-<project>`), one window per team."""
    name = "tmux"
    board_in_terminal = True

    def __init__(self, cfg, root):
        super().__init__(cfg, root)
        self.session = cfg.get("tmux_session") or f"teams-{project_slug(self.root)}"

    def available(self) -> bool:
        return shutil.which("tmux") is not None

    def _cmd(self, *args, timeout=10) -> str | None:
        r = _run(["tmux", *args], timeout=timeout)
        return r.stdout.strip() if r and r.returncode == 0 else None

    def _session_exists(self) -> bool:
        return self._cmd("has-session", "-t", f"={self.session}") is not None     # `=`: exact name, not a prefix

    def _window(self, title, cwd) -> dict | None:
        fresh = not self._session_exists()
        if fresh:
            out = self._cmd("new-session", "-d", "-s", self.session, "-n", title, "-c", str(cwd), "-P", "-F", "#{window_id}")
        else:
            out = self._cmd("new-window", "-d", "-t", f"={self.session}:", "-n", title, "-c", str(cwd), "-P", "-F", "#{window_id}")
        if not out:
            return None
        # A pane reaches the terminal attached to the session only through passthrough, and only when
        # its window allows it: `all` also covers a window nobody is looking at, which is every team
        # but one. The option is per window (a session-level one never reaches the panes) and panes
        # split off later inherit it.
        self._cmd("set-option", "-w", "-t", out, "allow-passthrough", "all")
        if fresh:
            self._prepare_session(out)
        return {"session": self.session, "window": out}

    def _prepare_session(self, window: str):
        """Once per session, so the terminal hosting it can be told what happens inside: the host's
        identity is copied into the session environment (a tmux server started from another terminal
        hands its own environment to every new pane), and an attach replays what the leads emitted
        before anyone was there to see it. Both are read back by bin/hostterm.py.

        The first window predates those variables: it is respawned once, and only when there is
        something to inherit — it holds nothing but a fresh shell at this point."""
        host = [(key, os.environ[key]) for key in HOST_TERMINAL_ENV if os.environ.get(key)]
        for key, value in host:                          # prefixed: tmux overwrites TERM_PROGRAM in every pane
            self._cmd("set-environment", "-t", self.session, hostterm.HOST_ENV_PREFIX + key, value)
        if not host:
            return
        config = self.cfg.get("_path")
        if config:                                       # what a pane emitted before anyone attached is lost:
            relay = " ".join([shlex.quote(sys.executable), shlex.quote(str(SELF)),   # replay it on every attach
                              "--config", shlex.quote(str(config)), "_relay"])
            self._cmd("set-hook", "-t", self.session, "client-attached", f"run-shell -b {shlex.quote(relay)}")
        self._cmd("respawn-window", "-k", "-t", window)

    def open(self, name, title, cwd, purpose="", command=None):
        return self._window(title, cwd)

    def open_tab(self, near, title, cwd):
        return self._window(title, cwd)

    def exists(self, handle):
        """Window ids are server-wide and reused after a server restart: a window only counts when
        it lives in this instance's session (`=`: exact name), or a stale handle would point at
        another instance's lead and `resume` would type into it."""
        out = self._cmd("list-windows", "-t", f"={handle['session']}", "-F", "#{window_id}") or ""
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
        if not self.exists(handle):                  # a reused window id would answer with another instance's tty
            return None
        return self._cmd("display-message", "-p", "-t", handle["window"], "#{pane_tty}") or None

    def select(self, handle):
        self._cmd("select-window", "-t", handle["window"])

    def close(self, handle):
        self._cmd("kill-window", "-t", handle["window"])

    def describe(self, handle):
        return f"{handle['session']}:{handle['window']}"

    def session_environ(self) -> dict:
        """The environment a pane of this session inherits, over the caller's own. `teams _relay`
        runs from tmux's `run-shell`, outside any pane, so its own environment says nothing about
        the terminal hosting the session."""
        environ = dict(os.environ)
        for line in (self._cmd("show-environment", "-t", f"={self.session}") or "").splitlines():
            if line.startswith("-"):
                environ.pop(line[1:], None)              # tmux marks a variable it removed
            elif "=" in line:
                key, _, value = line.partition("=")
                environ[key] = value
        return environ

    def attach_hint(self):
        return "" if os.environ.get("TMUX") else f"attach with: tmux attach -t {self.session}"

    def title(self, text):
        """tmux pushes its title to the terminal it is attached in (Warp names the tab with it)."""
        self._cmd("set-option", "-t", self.session, "set-titles", "on")
        self._cmd("set-option", "-t", self.session, "set-titles-string", text)

    def show(self, text):
        """The session's status bar, right side; the left side is widened so the session name is not
        cut to ten characters next to it."""
        self._cmd("set-option", "-t", self.session, "status-left-length", "40")
        self._cmd("set-option", "-t", self.session, "status-right", text)


def _tq(value) -> str:
    """One TOML basic string."""
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


class Warp(Driver):
    """Warp: one real tab per team in the ACTIVE window, opened from a tab config file.

    Warp exposes no way to type into a tab from outside, so the command is given when the tab is
    opened: `warp://tab_config/<stem>` runs `teams _run <team>`, which records its pid and then
    execs claude in the same process. That pid file is the only link to the tab (Warp answers no
    query), and it is what `exists`, `tty` and `close` read. The gain over running the teams
    inside tmux: each tab is a real pty, so the claude-code-warp plugin's escape sequences reach
    Warp and its sidebar shows the Claude icon and status of every team."""
    name = "warp"
    board_in_terminal = False
    types_commands = False

    def __init__(self, cfg, root):
        super().__init__(cfg, root)
        self.slug = project_slug(self.root)

    def available(self) -> bool:
        return os.environ.get("TERM_PROGRAM") == "WarpTerminal"

    def _stem(self, name: str) -> str:
        """Tab config file name = what `warp://tab_config/` matches; scoped by project."""
        return f"teams-{self.slug}-{name}"

    def _pid(self, handle: dict) -> int | None:
        return run_pid(self.root, handle["name"])

    def open(self, name, title, cwd, purpose="", command=None):
        if not command:
            return None                                  # nothing to type later: a tab without a command is useless
        stem, toml = self._stem(name), None
        try:
            pid_file(self.root, name).unlink(missing_ok=True)        # a stale pid would look alive
            WARP_TABS.mkdir(parents=True, exist_ok=True)
            toml = WARP_TABS / f"{stem}.toml"
            toml.write_text(
                "# generated by `teams up` — rewritten on every run, removed by `teams down`\n"
                f"name = {_tq(title)}\ntitle = {_tq(title)}\ncolor = {_tq(WARP_COLOR)}\n\n"
                '[[panes]]\nid = "main"\ntype = "terminal"\n'
                f"directory = {_tq(cwd)}\nis_focused = true\n"
                f"commands = [{_tq(command)}]\n")
        except OSError:
            return None
        r = _run(["open", f"warp://tab_config/{quote(stem, safe='')}"])   # no ?new_window: the ACTIVE window
        if not r or r.returncode != 0:
            toml.unlink(missing_ok=True)
            return None
        time.sleep(0.6)                                  # let Warp finish the tab before the next URI
        return {"stem": stem, "name": name}

    def exists(self, handle):
        pid = self._pid(handle)
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return "claude" in _ps(pid, "command=")

    def wait_ready(self, handle, timeout=15):
        """Ready = `teams _run` has written its pid file, right before exec'ing claude."""
        f = pid_file(self.root, handle["name"])
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if f.exists():
                return
            time.sleep(0.2)                              # Warp is slow to start a tab; give up silently

    def send(self, handle, text):
        return False                                     # Warp has no scripting API to type into a tab

    def tty(self, handle):
        pid = self._pid(handle)
        t = _ps(pid, "tty=") if pid else ""
        return f"/dev/{t}" if t and t != "??" else None

    def select(self, handle):
        pass                                             # the last tab opened has the focus; `up` opens the primary last

    def close(self, handle):
        pid, shell = self._pid(handle), run_shell_pid(self.root, handle["name"])
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                for _ in range(50):                      # up to 5 s, then insist
                    time.sleep(0.1)
                    os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass                                     # gone: the wait loop ends on the first failed kill(0)
        if shell:
            try:
                os.kill(shell, signal.SIGHUP)            # an interactive shell ignores SIGTERM; SIGHUP closes the tab
            except OSError:
                pass
        try:
            pid_file(self.root, handle["name"]).unlink(missing_ok=True)
            (WARP_TABS / f"{handle['stem']}.toml").unlink(missing_ok=True)
        except OSError:
            pass

    def describe(self, handle):
        pid = self._pid(handle)
        return f"warp tab {handle['stem']}" + (f" (pid {pid})" if pid else "")

    def attach_hint(self):
        return ("Tabs opened in the active Warp window; Warp cannot group tabs from a config: "
                "select them and right-click > New group with tabs.")


DRIVERS = {"programa": Programa, "warp": Warp, "tmux": Tmux, "manual": Manual}


def driver(name: str, cfg: dict, root: Path) -> Driver:
    if name not in DRIVERS:
        raise ValueError(f"unknown terminal driver {name!r} (expected one of {', '.join(NAMES)})")
    return DRIVERS[name](cfg, root)


def detect(cfg: dict, root: Path) -> Driver:
    """`terminal` in teams.json: programa | tmux | warp | manual | auto (default).
    auto = programa inside programa, else tmux when installed, else warp inside Warp, else manual.
    tmux comes first because one window per team in one tab stays the cheapest layout: the leads'
    hooks relay their status out of it (bin/hostterm.py), so the host terminal still shows the agent."""
    want = cfg.get("terminal", "auto")
    if want != "auto":
        return driver(want, cfg, root)
    for name in ("programa", "tmux", "warp"):
        d = driver(name, cfg, root)
        if d.available():
            return d
    return Manual(cfg, root)
