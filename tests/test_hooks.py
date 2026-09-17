from support import Fixture, ROOT
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
import sys
import hooklib
import storage
import tasklib


class Hooks(Fixture):
    def event(self, message, to='demo-backend', **extra):
        return {'session_id': 'session', 'tool_use_id': 'tool1', 'tool_name': 'SendMessage',
                'tool_input': {'to': to, 'message': message}, **extra}

    def handle(self, event, phase):
        return hooklib.handle(self.cfg['_path'], 'manager', {**event, 'hook_event_name': phase})

    def records(self):
        return [storage.read_json(path) for path in (self.root / '.state/messages').glob('*.json')]

    def test_subagent_message_is_allowed_before_tracking_or_protocol_validation(self):
        event = {'hook_event_name': 'PreToolUse', 'tool_name': 'SendMessage',
                 'tool_input': {'to': 'worker-simple-42', 'message': 'Please inspect the failing test'}}
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'bin/teams'), '_hook'],
            input=json.dumps(event), capture_output=True, text=True,
            env={**os.environ, 'TEAMS_TEAM': 'manager', 'TEAMS_CONFIG': str(self.cfg['_path'])})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})
        self.assertEqual(self.records(), [])

    def test_protocol_shaped_worker_message_does_not_change_ticket(self):
        tid = self.task()['id']
        event = self.event(f'TASK {tid} | implement', to='worker-simple')
        self.handle(event, 'PreToolUse'); self.handle(event, 'PostToolUse')
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'todo')
        self.assertEqual(self.records(), [])

    def test_free_form_team_message_passes_without_ticket_side_effects(self):
        self.handle(self.event('A quick question about your approach'), 'PreToolUse')
        self.assertEqual(self.records(), [])

    def test_missing_managed_ticket_is_an_explicit_pre_send_error(self):
        event = self.event('TASK T999 | implement', hook_event_name='PreToolUse')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'bin/teams'), '_hook'],
            input=json.dumps(event), capture_output=True, text=True,
            env={**os.environ, 'TEAMS_TEAM': 'manager', 'TEAMS_CONFIG': str(self.cfg['_path'])})
        self.assertEqual(result.returncode, 2)
        self.assertIn('T999', result.stderr)

    def test_failed_send_leaves_ticket_ready_and_success_normalizes_recipient(self):
        tid = self.task()['id']
        event = self.event(f'TASK {tid} | implement\ncriteria: preserve behavior')
        self.handle(event, 'PreToolUse')
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'todo')
        self.handle(event, 'PostToolUseFailure')
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'todo')
        self.assertEqual(self.records()[0]['state'], 'failed')
        self.handle(event, 'PostToolUse')
        ticket = tasklib.load(self.shared, tid)
        self.assertEqual((ticket['status'], ticket['team']), ('doing', 'backend'))
        self.assertIn('criteria: preserve behavior', (self.shared / 'LOG.md').read_text())

    def test_concurrent_replayed_success_is_applied_once(self):
        tid = self.task()['id']
        event = self.event(f'TASK {tid} | implement')
        self.handle(event, 'PreToolUse')
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: self.handle(event, 'PostToolUse'), range(20)))
        entries = tasklib.load(self.shared, tid)['log']
        self.assertEqual(sum('TASK' in line for line in entries), 1)
        self.assertEqual(len(self.records()), 1)

    def test_state_change_after_send_is_recorded_and_can_be_reconciled(self):
        tid = self.task()['id']
        event = self.event(f'TASK {tid} | implement')
        self.handle(event, 'PreToolUse')
        tasklib.update(self.shared, tid, {'status': 'backlog'})
        warning = self.handle(event, 'PostToolUse')
        self.assertIn('synchronization failed', warning)
        self.assertEqual(self.records()[0]['state'], 'sync_failed')
        self.assertTrue(self.records()[0]['sent'])
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'backlog')
        tasklib.update(self.shared, tid, {'status': 'todo'})
        self.handle(event, 'PostToolUse')
        self.assertEqual(self.records()[0]['state'], 'sent')
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'doing')

    def test_missing_tracking_ids_warn_and_preserve_sent_message(self):
        tid = self.task()['id']
        event = self.event(f'TASK {tid} | implement')
        event.pop('tool_use_id')
        self.assertIn('missing tracking', self.handle(event, 'PreToolUse'))
        self.assertIn('synchronization failed', self.handle(event, 'PostToolUse'))
        self.assertEqual(self.records()[0]['state'], 'sync_failed')
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'todo')

    def test_new_run_archives_old_sessions_and_ignores_late_old_callbacks(self):
        old_run = hooklib.begin_run(self.root)
        tid = self.task()['id']
        event = self.event(f'TASK {tid} | implement', hook_event_name='PreToolUse')
        hooklib.handle(self.cfg['_path'], 'manager', event, old_run)
        new_run = hooklib.begin_run(self.root)
        self.assertNotEqual(old_run, new_run)
        self.assertTrue(list((self.root / '.state/history').glob('*/sessions/manager.json')))
        self.assertTrue(list((self.root / '.state/history').glob('*/messages/*.json')))
        hooklib.handle(self.cfg['_path'], 'manager', {**event, 'hook_event_name': 'PostToolUse'}, old_run)
        self.assertEqual(tasklib.load(self.shared, tid)['status'], 'todo')
        hooklib.handle(self.cfg['_path'], 'manager', {'hook_event_name': 'SessionStart', 'session_id': 'new'}, new_run)
        self.assertEqual(storage.read_json(self.root / '.state/sessions/manager.json')['sessions'], ['new'])


class Relayed(Fixture):
    """The hooks the host terminal needs (Notification, PermissionRequest) carry no team state."""

    def run_hook(self, event, **env):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'bin/teams'), '_hook'],
                              input=json.dumps(event), capture_output=True, text=True,
                              env={**os.environ, 'TEAMS_TEAM': 'manager',
                                   'TEAMS_CONFIG': str(self.cfg['_path']), **env})

    def test_events_the_launcher_does_not_know_are_recorded_but_change_nothing(self):
        for name in ('Notification', 'PermissionRequest'):
            self.assertIsNone(hooklib.handle(self.cfg['_path'], 'manager',
                                             {'hook_event_name': name, 'session_id': 's1'}))
        session = storage.read_json(self.root / '.state/sessions/manager.json')
        self.assertEqual(session['status'], '?')            # liveness is untouched by a relay-only event
        self.assertEqual(session['sessions'], ['s1'])

    def test_hook_output_carries_the_host_sequence_next_to_a_warning(self):
        warp = {'TMUX': '/tmp/tmux-501/default,1,0', 'TERM_PROGRAM': 'WarpTerminal',
                'WARP_CLI_AGENT_PROTOCOL_VERSION': '1'}
        plain = self.run_hook({'hook_event_name': 'SessionStart', 'session_id': 's1', 'cwd': str(self.repo)}, **warp)
        self.assertEqual(plain.returncode, 0, plain.stderr)
        sequence = json.loads(plain.stdout)['terminalSequence']
        self.assertTrue(sequence.startswith('\x1bPtmux;\x1b\x1b]777;notify;warp://cli-agent;'), repr(sequence[:40]))
        self.assertIn('"event":"session_start"', sequence)
        self.assertIn('"plugin_version":"agent-teams ', sequence)
        self.assertNotIn('systemMessage', json.loads(plain.stdout))
        # an event that both warns and has something to relay keeps the two side by side
        both = self.run_hook({'hook_event_name': 'PostToolUse', 'session_id': 's1', 'cwd': str(self.repo),
                              'tool_name': 'SendMessage',
                              'tool_input': {'to': 'backend', 'message': 'DONE T1 | finished'}}, **warp)
        out = json.loads(both.stdout)
        self.assertIn('ticket synchronization failed', out['systemMessage'])
        self.assertIn('"event":"tool_complete"', out['terminalSequence'])

    def test_outside_tmux_the_hook_output_is_what_it_always_was(self):
        result = self.run_hook({'hook_event_name': 'SessionStart', 'session_id': 's1'},
                               TMUX='', TERM_PROGRAM='WarpTerminal')
        self.assertEqual(json.loads(result.stdout), {})      # the host's own plugin already has this event
