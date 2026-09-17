"""Re-emit an agent's lifecycle to the terminal hosting the multiplexer.

A terminal that draws agent status (Warp's sidebar) learns it from an escape sequence its own
Claude Code plugin writes to the session's pty.  Inside tmux that pty belongs to tmux, which eats
the sequence, so every team shows up as a plain shell.  The leads' hooks run *inside* those panes:
`teams _hook` rebuilds the payload the host expects and hands it back to Claude Code in the
`terminalSequence` field, wrapped in tmux's passthrough envelope.  The tab running `tmux attach`
then shows the agent and its state, and the teams stay where they are.

    seq = terminal_sequence(event, engine_version=VERSION)   # None: nothing to relay

Nothing here raises: a relay that fails is a missing icon, never a broken hook.  Outside tmux it
relays nothing at all, because the host's own plugin is already delivering the same events.
"""
import json
import os
import re
import time

HOST_ENV_PREFIX = "TEAMS_HOST_"    # tmux rewrites TERM_PROGRAM inside a pane: the host's own values are copied
                                   # into the session under this prefix when the session is created
MIN_CLAUDE_VERSION = (2, 1, 141)   # first Claude Code accepting the `terminalSequence` hook output field
PROTOCOL_VERSION = 1               # warp://cli-agent payload version this module speaks
CAP = 200                          # the host shows one short line; the plugin truncates the same way
STOP_SETTLE = 0.3                  # Stop fires before the turn is flushed to the transcript


def host_env(environ, key: str) -> str:
    """What the terminal hosting the multiplexer exports for `key`: the copy the launcher put in the
    session environment (see Tmux._prepare_session), else the variable itself for a session that
    inherited the host's environment untouched."""
    return environ.get(HOST_ENV_PREFIX + key) or environ.get(key, "")


def _clip(text, cap: int = CAP) -> str:
    text = str(text or "")
    return text if len(text) <= cap else text[:cap - 3] + "..."


def _version(raw: str):
    """(2, 1, 141) out of "claude 2.1.141", "v2.1.141"… None when there is no version in it."""
    found = re.search(r"(\d+)\.(\d+)\.(\d+)", raw or "")
    return tuple(int(part) for part in found.groups()) if found else None


def _tmux_passthrough(sequence: str) -> str:
    """tmux forwards a sequence only inside its DCS envelope, with every ESC doubled (and only when
    the session allows passthrough — the tmux driver sets that on the session it creates)."""
    return "\x1bPtmux;" + sequence.replace("\x1b", "\x1b\x1b") + "\x1b\\"


def _transcript_tail(path, settle: float = None) -> tuple[str, str]:
    """Last human prompt and last assistant answer of a Claude transcript (JSONL), chosen as the
    Warp plugin's on-stop.sh does: a `user` entry counts only when it carries text, so tool results
    are skipped. Unreadable transcript: two empty strings."""
    query = response = ""
    try:
        if not isinstance(path, str) or not os.path.isfile(path):
            return query, response
        time.sleep(STOP_SETTLE if settle is None else settle)
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                content = (entry.get("message") or {}).get("content")
                kind = entry.get("type")
                if kind == "user":
                    if isinstance(content, str) and content:
                        query = content
                    elif isinstance(content, list):
                        text = _texts(content)
                        if text:
                            query = text
                elif kind == "assistant" and content:
                    response = _texts(content) if isinstance(content, list) else str(content)
    except (OSError, TypeError, ValueError):
        pass
    return query, response


def _texts(blocks) -> str:
    return " ".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")


def warp_sequence(event: dict, environ, engine_version: str) -> str | None:
    """The OSC 777 `warp://cli-agent` payload of the claude-code-warp plugin (mirrors its 2.2.0
    scripts, so Warp reads exactly what it reads from its own hooks).

    A replayed event (see replay_sequence) may carry two keys no real hook sends: `summary`, for a
    state whose wording cannot be derived, and `settle`, to skip the wait for a transcript that was
    flushed long ago."""
    if not host_env(environ, "WARP_CLI_AGENT_PROTOCOL_VERSION"):
        return None                                  # this Warp does not speak the structured protocol
    cwd = event.get("cwd") or ""
    body = {"v": _protocol(environ), "agent": "claude", "event": "",
            "session_id": event.get("session_id") or "", "cwd": cwd, "project": os.path.basename(cwd)}
    name = event.get("hook_event_name")
    if name == "SessionStart":
        body["event"] = "session_start"
        body["plugin_version"] = f"agent-teams {engine_version}".strip()
    elif name == "UserPromptSubmit":
        body["event"] = "prompt_submit"
        body["query"] = _clip(event.get("prompt"))
    elif name == "Stop":
        if event.get("stop_hook_active"):
            return None                              # a stop hook is already running: the plugin skips it too
        query, response = _transcript_tail(event.get("transcript_path"), event.get("settle"))
        body["event"] = "stop"
        body["query"], body["response"] = _clip(query), _clip(response)
        body["transcript_path"] = str(event.get("transcript_path") or "")
    elif name == "Notification":
        body["event"] = event.get("notification_type") or "unknown"
        body["summary"] = event.get("message") or "Input needed"
    elif name == "PermissionRequest":
        tool = event.get("tool_name") or "unknown"
        tool_input = event.get("tool_input")
        if not isinstance(tool_input, dict):
            tool_input = {}
        preview = tool_input.get("command") or tool_input.get("file_path") \
            or json.dumps(tool_input, separators=(",", ":"))[:80]
        body["event"] = "permission_request"
        body["summary"] = event.get("summary") or \
            f"Wants to run {tool}" + (f": {_clip(preview, 120)}" if preview else "")
        body["tool_name"] = tool
        body["tool_input"] = tool_input
    elif name == "PostToolUse":
        body["event"] = "tool_complete"
        body["tool_name"] = event.get("tool_name") or ""
    else:
        return None                                  # an event the host has no state for
    return "\x1b]777;notify;warp://cli-agent;" + json.dumps(body, separators=(",", ":")) + "\x07"


def _protocol(environ) -> int:
    """min(what we speak, what the host advertises), as the plugin negotiates it."""
    advertised = host_env(environ, "WARP_CLI_AGENT_PROTOCOL_VERSION")
    return min(PROTOCOL_VERSION, int(advertised)) if advertised.isdigit() else PROTOCOL_VERSION


HOSTS = {"WarpTerminal": warp_sequence}              # one entry per terminal that draws agent status

REPLAY = {"working": {"hook_event_name": "UserPromptSubmit", "prompt": ""},
          "idle": {"hook_event_name": "Stop", "settle": 0},
          "blocked": {"hook_event_name": "PermissionRequest", "summary": "Waiting for input"}}


def _host(environ):
    """The payload builder for the terminal hosting this session, or None when it is not one we know."""
    return HOSTS.get(host_env(environ, "TERM_PROGRAM"))


def _accepts_output_field(environ) -> bool:
    """Claude Code only learned the `terminalSequence` hook output field in 2.1.141. An absent
    version means a build old enough not to export one, or new enough not to need it: assume new."""
    version = _version(environ.get("CLAUDE_CODE_VERSION", ""))
    return version is None or version >= MIN_CLAUDE_VERSION


def replay_sequence(session_record: dict, environ=os.environ, engine_version: str = "") -> str | None:
    """What to write into a team's terminal when someone attaches to the multiplexer.

    Passthrough only reaches a client that is already attached, and a lead announces itself once, at
    SessionStart, usually long before anyone attaches: the host would stay blank until that team's
    next hook. This rebuilds what the host missed out of `.state/sessions/<team>.json` — the session
    exists, and this is its state — as two sequences, each wrapped on its own. None when the team has
    nothing to show (gone, or a state we cannot name)."""
    try:
        host, shape = _host(environ), REPLAY.get(session_record.get("status"))
        if host is None or shape is None:
            return None
        common = {key: session_record.get(key) for key in ("session_id", "cwd", "transcript_path")}
        start = host({**common, "hook_event_name": "SessionStart"}, environ, engine_version)
        state = host({**common, **shape}, environ, engine_version)
        return _tmux_passthrough(start) + _tmux_passthrough(state) if start and state else None
    except Exception:                                # a replay is never worth failing an attach over
        return None


def terminal_sequence(event: dict, environ=os.environ, engine_version: str = "") -> str | None:
    """What to hand Claude Code as `terminalSequence`, or None when there is nothing to relay:
    outside tmux the host's own plugin already delivers these events (never send them twice), an
    unrecognised host has no protocol to speak, and a Claude Code older than 2.1.141 rejects the
    field (an absent version is assumed recent, as the version is only exported by newer builds)."""
    try:
        if not environ.get("TMUX") or not _accepts_output_field(environ):
            return None
        host = _host(environ)                        # "tmux" inside a pane: only the copy identifies the host
        if host is None:
            return None
        sequence = host(event, environ, engine_version)
        return _tmux_passthrough(sequence) if sequence else None
    except Exception:                                # a relay is never worth failing a hook over
        return None
