"""Track current lead sessions and recognized inter-team ticket messages."""
import hashlib
import json
from pathlib import Path
import uuid
import storage
import tasklib


def run_id(root):
    return storage.read_json(Path(root) / '.state' / 'run.json').get('id')


def begin_run(root):
    """A fresh up archives prior session/message records; resume leaves them alone."""
    state = Path(root) / '.state'
    with storage.locked(state / 'lifecycle.lock'), storage.locked(state / 'messages.lock'):
        stamp = tasklib.now().replace(':', '-') + '-' + uuid.uuid4().hex[:8]
        archive = state / 'history' / stamp
        for name in ('sessions', 'messages'):
            source = state / name
            if source.exists():
                archive.mkdir(parents=True, exist_ok=True)
                source.rename(archive / name)
        key = uuid.uuid4().hex
        storage.write_json(state / 'run.json', {'id': key, 'started': tasklib.now()})
        return key


def _stale(root, expected):
    return expected is not None and run_id(root) != expected


def _log(shared, team, to, message, key):
    with storage.locked(shared / '.locks' / 'log.lock'):
        log = shared / 'LOG.md'
        marker = f'<!-- event:{key} -->'
        existing = log.read_text() if log.exists() else ''
        if marker not in existing:
            header, _, body = message.partition('\n')
            lines = [f'{tasklib.now()} {team} → {to} | {header}']
            lines.extend('    ' + line for line in body.splitlines()[:5])
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open('a') as out:
                out.write('\n'.join([*lines, marker]) + '\n')


def handle(config, team, event, expected_run=None):
    cfg = json.loads(Path(config).read_text())
    root = Path(config).resolve().parent
    state = root / '.state'
    shared = (root / cfg.get('shared_dir', 'shared')).resolve()
    names = [t['name'] for t in cfg['teams'] if t.get('enabled', True)]
    primary = next(t['name'] for t in cfg['teams'] if t.get('primary') and t.get('enabled', True))
    if team not in names or event.get('agent_id'):
        return  # Worker-local hooks are outside the lead roster.
    ev = event.get('hook_event_name')
    with storage.locked(state / 'lifecycle.lock'):
        if _stale(root, expected_run):
            return
        session_file = state / 'sessions' / f'{team}.json'
        session = storage.read_json(session_file)
        session.update({k: event[k] for k in ('session_id', 'transcript_path', 'cwd') if event.get(k)})
        session['status'] = {'SessionStart': 'idle', 'UserPromptSubmit': 'working',
                            'Stop': 'idle', 'SessionEnd': 'gone'}.get(ev, session.get('status', '?'))
        session['updated'] = tasklib.now()
        sessions = session.setdefault('sessions', [])
        if event.get('session_id') and event['session_id'] not in sessions:
            sessions.append(event['session_id'])
        storage.write_json(session_file, session)
    if event.get('tool_name') != 'SendMessage':
        return
    tool = event.get('tool_input', {})
    to = tool.get('to', '')
    try:
        to = tasklib.canonical_team(to, names, cfg.get('session_prefix', ''))
    except (ValueError, TypeError, AttributeError):
        return  # Native lead↔worker messages are not inter-team ticket traffic.
    message = tool.get('message')
    if not isinstance(message, str):
        return
    header = message.split('\n', 1)[0]
    if not tasklib.MESSAGE.fullmatch(header.strip()):
        return  # Free-form messages are delivered without ticket side effects.
    tracked = bool(event.get('session_id') and event.get('tool_use_id'))
    key = (hashlib.sha256(f"{event['session_id']}:{event['tool_use_id']}".encode()).hexdigest()
           if tracked else 'untracked-' + uuid.uuid4().hex)
    path = state / 'messages' / f'{key}.json'
    with storage.locked(state / 'messages.lock'):
        if _stale(root, expected_run):
            return
        previous = storage.read_json(path)
        if previous.get('state') == 'sent':
            return
        record = {'id': key, 'sender': team, 'to': to, 'message': message, 'at': tasklib.now()}
        if ev == 'PreToolUse':
            tasklib.apply_message(shared, team, to, header, primary=primary,
                                  event_id=key if tracked else None, validate_only=True)
            if not tracked:
                return 'teams: message will be sent, but missing tracking IDs prevent replay-safe ticket updates'
            storage.write_json(path, {**record, 'state': 'attempted'})
        elif ev == 'PostToolUseFailure' or (isinstance(event.get('tool_response'), dict)
                                           and event['tool_response'].get('is_error')):
            storage.write_json(path, {**record, 'state': 'failed', 'error': event.get('error', 'tool error')})
        elif ev == 'PostToolUse':
            try:
                if not tracked:
                    raise ValueError('missing session_id/tool_use_id; ticket update skipped')
                tasklib.apply_message(shared, team, to, header, primary=primary, event_id=key)
                _log(shared, team, to, message, key)
            except (OSError, ValueError) as exc:
                storage.write_json(path, {**record, 'state': 'sync_failed', 'sent': True, 'error': str(exc)})
                return f'teams: message sent but ticket synchronization failed: {exc}; recorded in {path}'
            storage.write_json(path, {**record, 'state': 'sent'})
