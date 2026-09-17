from support import Fixture
import json
import hostterm

WARP = {'TMUX': '/tmp/tmux-501/default,1,0', 'TERM_PROGRAM': 'WarpTerminal',
        'WARP_CLI_AGENT_PROTOCOL_VERSION': '1'}
BASE = {'session_id': 'sess-1', 'cwd': '/tmp/some project'}


class Relay(Fixture):
    """bin/hostterm rebuilds, inside tmux, the status the host terminal's own plugin never sees."""

    def setUp(self):
        super().setUp()
        hostterm.STOP_SETTLE = 0            # the real one waits for Claude to flush the transcript
        self.addCleanup(setattr, hostterm, 'STOP_SETTLE', 0.3)

    def payload(self, event, environ=None, version='0.1.0'):
        """The JSON the host receives, unwrapped from the tmux envelope and the OSC."""
        sequence = hostterm.terminal_sequence({**BASE, **event}, {**WARP, **(environ or {})}, version)
        if sequence is None:
            return None
        self.assertTrue(sequence.startswith('\x1bPtmux;'), repr(sequence[:20]))
        self.assertTrue(sequence.endswith('\x1b\\'), repr(sequence[-4:]))
        inner = sequence[len('\x1bPtmux;'):-2].replace('\x1b\x1b', '\x1b')
        self.assertTrue(inner.startswith('\x1b]777;notify;warp://cli-agent;') and inner.endswith('\x07'))
        return json.loads(inner.split('warp://cli-agent;', 1)[1][:-1])

    def test_every_esc_is_doubled_inside_the_tmux_envelope(self):
        sequence = hostterm.terminal_sequence({**BASE, 'hook_event_name': 'SessionStart'}, WARP, '0.1.0')
        self.assertNotIn('\x1b\x1b\x1b', sequence)                  # exactly two, never three
        self.assertEqual(sequence.count('\x1b\x1b'), 1)             # the payload itself holds one ESC
        self.assertEqual(hostterm._tmux_passthrough('\x1bA\x1bB'), '\x1bPtmux;\x1b\x1bA\x1b\x1bB\x1b\\')

    def test_session_start_names_the_engine_as_the_plugin(self):
        body = self.payload({'hook_event_name': 'SessionStart'})
        self.assertEqual(body, {'v': 1, 'agent': 'claude', 'event': 'session_start', 'session_id': 'sess-1',
                                'cwd': '/tmp/some project', 'project': 'some project',
                                'plugin_version': 'agent-teams 0.1.0'})

    def test_prompt_submit_carries_a_truncated_query(self):
        body = self.payload({'hook_event_name': 'UserPromptSubmit', 'prompt': 'q' * 400})
        self.assertEqual(body['event'], 'prompt_submit')
        self.assertEqual(len(body['query']), 200)
        self.assertTrue(body['query'].endswith('...'))
        short = self.payload({'hook_event_name': 'UserPromptSubmit', 'prompt': 'hello'})
        self.assertEqual(short['query'], 'hello')

    def test_stop_reads_the_last_exchange_from_the_transcript(self):
        path = self.root / 'transcript.jsonl'
        path.write_text('\n'.join(json.dumps(entry) for entry in [
            {'type': 'user', 'message': {'content': 'first question'}},
            {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'first answer'}]}},
            {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': 'ignored'}]}},
            {'type': 'user', 'message': {'content': [{'type': 'text', 'text': 'second question'}]}},
            {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'second answer'}]}},
        ]) + '\n')
        body = self.payload({'hook_event_name': 'Stop', 'transcript_path': str(path)})
        self.assertEqual(body['event'], 'stop')
        self.assertEqual(body['query'], 'second question')          # the tool result is not a prompt
        self.assertEqual(body['response'], 'second answer')
        self.assertEqual(body['transcript_path'], str(path))
        missing = self.payload({'hook_event_name': 'Stop', 'transcript_path': str(self.root / 'gone.jsonl')})
        self.assertEqual((missing['query'], missing['response']), ('', ''))

    def test_stop_is_silent_while_another_stop_hook_runs(self):
        self.assertIsNone(self.payload({'hook_event_name': 'Stop', 'stop_hook_active': True}))

    def test_notification_becomes_its_own_event_name(self):
        body = self.payload({'hook_event_name': 'Notification', 'notification_type': 'idle_prompt',
                             'message': 'Claude is waiting'})
        self.assertEqual((body['event'], body['summary']), ('idle_prompt', 'Claude is waiting'))
        bare = self.payload({'hook_event_name': 'Notification'})
        self.assertEqual((bare['event'], bare['summary']), ('unknown', 'Input needed'))

    def test_permission_request_summarizes_what_is_blocked(self):
        body = self.payload({'hook_event_name': 'PermissionRequest', 'tool_name': 'Bash',
                             'tool_input': {'command': 'rm -rf ' + 'y' * 200}})
        self.assertEqual(body['event'], 'permission_request')
        self.assertEqual(body['tool_name'], 'Bash')
        self.assertTrue(body['summary'].startswith('Wants to run Bash: rm -rf yyy'))
        self.assertEqual(len(body['summary']), len('Wants to run Bash: ') + 120)
        self.assertEqual(self.payload({'hook_event_name': 'PermissionRequest', 'tool_name': 'Edit',
                                       'tool_input': {'file_path': '/tmp/a.py'}})['summary'],
                         'Wants to run Edit: /tmp/a.py')
        other = self.payload({'hook_event_name': 'PermissionRequest', 'tool_name': 'WebFetch',
                              'tool_input': {'url': 'https://example.com'}})
        self.assertEqual(other['summary'], 'Wants to run WebFetch: {"url":"https://example.com"}')
        self.assertEqual(other['tool_input'], {'url': 'https://example.com'})

    def test_post_tool_use_reports_the_tool_that_finished(self):
        body = self.payload({'hook_event_name': 'PostToolUse', 'tool_name': 'SendMessage'})
        self.assertEqual((body['event'], body['tool_name']), ('tool_complete', 'SendMessage'))

    def test_events_the_host_has_no_state_for_are_dropped(self):
        for name in ('SessionEnd', 'PreToolUse', 'PostToolUseFailure', None):
            self.assertIsNone(self.payload({'hook_event_name': name}), name)

    def replay(self, record, environ=None):
        """The payloads a client attaching to the multiplexer receives for one team."""
        sequence = hostterm.replay_sequence(record, {**WARP, **(environ or {})}, '0.1.0')
        if sequence is None:
            return None
        parts = [p for p in sequence.split('\x1bPtmux;') if p]
        return [json.loads(p[:-2].replace('\x1b\x1b', '\x1b').split('warp://cli-agent;', 1)[1][:-1]) for p in parts]

    def test_an_attaching_client_is_told_the_session_exists_and_what_it_is_doing(self):
        record = {'session_id': 'sess-1', 'cwd': '/tmp/some project', 'status': 'working'}
        start, state = self.replay(record)
        self.assertEqual(start['event'], 'session_start')            # the host learns the agent first
        self.assertEqual(start['session_id'], 'sess-1')
        self.assertEqual((state['event'], state['query']), ('prompt_submit', ''))

    def test_an_idle_team_replays_its_last_exchange(self):
        path = self.root / 'transcript.jsonl'
        path.write_text(json.dumps({'type': 'user', 'message': {'content': 'the question'}}) + '\n' +
                        json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'the answer'}]}}) + '\n')
        hostterm.STOP_SETTLE = 9999                                  # a replay never waits for a flush
        start, state = self.replay({'session_id': 's', 'cwd': '/tmp/p', 'status': 'idle',
                                    'transcript_path': str(path)})
        self.assertEqual(state['event'], 'stop')
        self.assertEqual((state['query'], state['response']), ('the question', 'the answer'))

    def test_a_blocked_team_replays_as_waiting_for_input(self):
        start, state = self.replay({'session_id': 's', 'cwd': '/tmp/p', 'status': 'blocked'})
        self.assertEqual((state['event'], state['summary']), ('permission_request', 'Waiting for input'))

    def test_a_team_with_nothing_to_show_replays_nothing(self):
        for record in ({'status': 'gone'}, {'status': '?'}, {}, {'status': 'idle'}):
            expected = None if record.get('status') != 'idle' else 2
            got = self.replay(record)
            self.assertEqual(got if got is None else len(got), expected, record)
        self.assertIsNone(hostterm.replay_sequence({'status': 'idle'}, {'TERM_PROGRAM': 'Apple_Terminal'}))

    def test_nothing_is_relayed_outside_tmux_or_to_an_unknown_host(self):
        event = {**BASE, 'hook_event_name': 'SessionStart'}
        outside = {k: v for k, v in WARP.items() if k != 'TMUX'}
        self.assertIsNone(hostterm.terminal_sequence(event, outside))     # the host plugin delivers it itself
        self.assertIsNone(hostterm.terminal_sequence(event, {**WARP, 'TERM_PROGRAM': 'Apple_Terminal'}))
        self.assertIsNone(hostterm.terminal_sequence(event, {'TMUX': '/tmp/s'}))
        without_protocol = {k: v for k, v in WARP.items() if k != 'WARP_CLI_AGENT_PROTOCOL_VERSION'}
        self.assertIsNone(hostterm.terminal_sequence(event, without_protocol))

    def test_the_host_is_read_from_the_copy_tmux_cannot_overwrite(self):
        """Inside a pane TERM_PROGRAM is always "tmux": only what the launcher copied names the host."""
        event = {**BASE, 'hook_event_name': 'SessionStart'}
        inside = {'TMUX': '/tmp/s', 'TERM_PROGRAM': 'tmux', 'TERM_PROGRAM_VERSION': '3.7c',
                  'TEAMS_HOST_TERM_PROGRAM': 'WarpTerminal',
                  'TEAMS_HOST_WARP_CLI_AGENT_PROTOCOL_VERSION': '1'}
        self.assertIsNotNone(hostterm.terminal_sequence(event, inside))
        without_copy = {k: v for k, v in inside.items() if not k.startswith('TEAMS_HOST_')}
        self.assertIsNone(hostterm.terminal_sequence(event, without_copy))      # host unknown: relay nothing
        self.assertEqual(hostterm.host_env(inside, 'TERM_PROGRAM'), 'WarpTerminal')
        self.assertEqual(hostterm.host_env({'TERM_PROGRAM': 'WarpTerminal'}, 'TERM_PROGRAM'), 'WarpTerminal')
        self.assertEqual(hostterm.host_env({}, 'TERM_PROGRAM'), '')

    def test_only_a_claude_code_that_accepts_the_field_is_given_one(self):
        event = {'hook_event_name': 'SessionStart'}
        self.assertIsNone(self.payload(event, {'CLAUDE_CODE_VERSION': '2.1.100'}))
        self.assertIsNone(self.payload(event, {'CLAUDE_CODE_VERSION': 'claude 2.0.999'}))
        self.assertIsNotNone(self.payload(event, {'CLAUDE_CODE_VERSION': '2.1.141'}))
        self.assertIsNotNone(self.payload(event, {'CLAUDE_CODE_VERSION': 'claude 2.1.273 (Claude Code)'}))
        self.assertIsNotNone(self.payload(event, {'CLAUDE_CODE_VERSION': 'unknown'}))   # unreadable: assume recent
        self.assertIsNotNone(self.payload(event))                                       # absent: assume recent

    def test_a_broken_event_costs_the_icon_not_the_hook(self):
        self.assertIsNone(hostterm.terminal_sequence('not an event', WARP))
        odd = self.payload({'hook_event_name': 'Stop', 'transcript_path': 42})
        self.assertEqual((odd['transcript_path'], odd['query']), ('42', ''))   # nothing to read, still valid JSON
        self.assertEqual(self.payload({'hook_event_name': 'PermissionRequest', 'tool_name': 'Bash',
                                       'tool_input': 'not a dict'})['summary'], 'Wants to run Bash: {}')
