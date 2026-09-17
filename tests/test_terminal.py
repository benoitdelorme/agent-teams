from support import Fixture
from unittest.mock import patch
from types import SimpleNamespace
import os
import shlex
import sys
import terminal


class Detect(Fixture):
    def test_auto_prefers_programa_then_tmux_then_warp_then_manual(self):
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': 'surface:1', 'PROGRAMA_SOCKET_PATH': '/tmp/s',
                                     'TERM_PROGRAM': 'WarpTerminal'}):
            self.assertEqual(terminal.detect({}, self.root).name, 'programa')
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': '', 'PROGRAMA_SOCKET_PATH': '', 'TERM_PROGRAM': 'WarpTerminal'}):
            with patch.object(terminal.shutil, 'which', return_value='/usr/bin/tmux'):
                self.assertEqual(terminal.detect({}, self.root).name, 'tmux')   # one tab, status relayed out of it
            with patch.object(terminal.shutil, 'which', return_value=None):
                self.assertEqual(terminal.detect({}, self.root).name, 'warp')   # no tmux: one real tab per team
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': '', 'PROGRAMA_SOCKET_PATH': '', 'TERM_PROGRAM': 'Apple_Terminal'}):
            with patch.object(terminal.shutil, 'which', return_value='/usr/bin/tmux'):
                self.assertEqual(terminal.detect({}, self.root).name, 'tmux')
            with patch.object(terminal.shutil, 'which', return_value=None):
                self.assertEqual(terminal.detect({}, self.root).name, 'manual')

    def test_explicit_choice_wins_and_unknown_names_are_rejected(self):
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': 'surface:1', 'PROGRAMA_SOCKET_PATH': '/tmp/s'}):
            self.assertEqual(terminal.detect({'terminal': 'tmux'}, self.root).name, 'tmux')
        with patch.dict(os.environ, {'TERM_PROGRAM': 'Apple_Terminal'}):
            self.assertEqual(terminal.detect({'terminal': 'warp'}, self.root).name, 'warp')   # chosen, not detected
        with self.assertRaises(ValueError):
            terminal.driver('screen', {}, self.root)


class Tmux(Fixture):
    def calls(self, outputs):
        """Patch subprocess so each tmux call returns the next canned stdout; record argv."""
        recorded = []
        def fake_run(args, **kw):
            recorded.append(args)
            out = outputs.pop(0) if outputs else ''
            return SimpleNamespace(returncode=0 if out is not None else 1, stdout=out or '', stderr='')
        return recorded, patch.object(terminal.subprocess, 'run', side_effect=fake_run)

    def test_session_is_named_after_the_project_and_windows_are_created_in_it(self):
        drv = terminal.Tmux({}, self.root / 'my Project' / '.teams')
        self.assertEqual(drv.session, 'teams-my-project')
        recorded, patcher = self.calls([None, '@7', '', '', '@8', ''])   # has-session fails, new-session, set-option, has-session ok, new-window
        with patcher, patch.dict(os.environ, {}, clear=True):        # no host terminal to record
            first = drv.open('backend', 'Backend', self.repo)
            second = drv.open('manager', 'Manager', self.root)
        self.assertEqual(first, {'session': 'teams-my-project', 'window': '@7'})
        self.assertEqual(second['window'], '@8')
        self.assertEqual(recorded[1][:5], ['tmux', 'new-session', '-d', '-s', 'teams-my-project'])
        self.assertEqual(recorded[4][:5], ['tmux', 'new-window', '-d', '-t', '=teams-my-project:'])   # exact session, not a prefix
        self.assertEqual(terminal.Tmux({}, self.root / 'flat-project').session, 'teams-flat-project')  # config at the project root

    def test_a_new_session_can_pass_a_sequence_out_and_knows_its_host(self):
        """The leads' hooks relay their status to the terminal the session is attached to."""
        drv = terminal.Tmux({'_path': self.root / 'teams.json'}, self.root / 'my Project' / '.teams')
        host = {'TERM_PROGRAM': 'WarpTerminal', 'TERM_PROGRAM_VERSION': '1.2',
                'WARP_CLI_AGENT_PROTOCOL_VERSION': '1', 'WARP_CLIENT_VERSION': 'v0.2026'}
        recorded, patcher = self.calls([None, '@7', '', '', '', '', '', '', '', '', '@8', ''])
        with patcher, patch.dict(os.environ, host, clear=True):
            drv.open('backend', 'Backend', self.repo)
            drv.open('manager', 'Manager', self.root)                  # second team: session already prepared
        self.assertEqual(recorded[2], ['tmux', 'set-option', '-w', '-t', '@7', 'allow-passthrough', 'all'])
        self.assertEqual(recorded[3:7], [['tmux', 'set-environment', '-t', 'teams-my-project',
                                          'TEAMS_HOST_' + key, value] for key, value in host.items()])
        # prefixed on purpose: tmux sets TERM_PROGRAM=tmux in every pane, whatever the session says
        hook = recorded[7]
        self.assertEqual(hook[:5], ['tmux', 'set-hook', '-t', 'teams-my-project', 'client-attached'])
        command, background, line = shlex.split(hook[5])                          # tmux parses the hook value
        self.assertEqual((command, background), ('run-shell', '-b'))
        self.assertEqual(shlex.split(line),                                       # the shell runs this on attach
                         [sys.executable, str(terminal.SELF), '--config', str(self.root / 'teams.json'), '_relay'])
        self.assertEqual(recorded[8], ['tmux', 'respawn-window', '-k', '-t', '@7'])   # window 1 predates them
        self.assertEqual([c[1] for c in recorded[9:]], ['has-session', 'new-window', 'set-option'])
        self.assertEqual(recorded[11][:5], ['tmux', 'set-option', '-w', '-t', '@8'])   # every window, once

    def test_a_session_without_a_known_host_is_only_opened_for_passthrough(self):
        drv = terminal.Tmux({}, self.root / 'my Project' / '.teams')
        recorded, patcher = self.calls([None, '@7', '', ''])
        with patcher, patch.dict(os.environ, {}, clear=True):
            drv.open('backend', 'Backend', self.repo)
        self.assertEqual([c[1] for c in recorded], ['has-session', 'new-session', 'set-option'])
        self.assertEqual(recorded[2], ['tmux', 'set-option', '-w', '-t', '@7', 'allow-passthrough', 'all'])

    def test_wait_ready_matches_a_prompt_whose_trailing_space_was_stripped(self):
        drv = terminal.Tmux({'tmux_session': 's'}, self.root)
        recorded, patcher = self.calls(['$ ls\nfile\n$', ''])          # capture-pane strips the trailing space of "$ "
        with patcher:
            drv.wait_ready({'session': 's', 'window': '@1'}, timeout=2)
        self.assertEqual(recorded[0][:3], ['tmux', 'capture-pane', '-p'])
        self.assertEqual(len(recorded), 1)                                 # matched on the first capture

    def test_send_types_the_text_literally_then_enter(self):
        drv = terminal.Tmux({'tmux_session': 's'}, self.root)
        recorded, patcher = self.calls(['', ''])
        with patcher:
            self.assertTrue(drv.send({'session': 's', 'window': '@1'}, 'claude -n backend\n'))
        self.assertEqual(recorded[0], ['tmux', 'send-keys', '-t', '@1', '-l', '--', 'claude -n backend'])
        self.assertEqual(recorded[1], ['tmux', 'send-keys', '-t', '@1', 'Enter'])

    def test_failed_commands_never_raise(self):
        drv = terminal.Tmux({'tmux_session': 's'}, self.root)
        with patch.object(terminal.subprocess, 'run', side_effect=OSError('no tmux')):
            self.assertIsNone(drv.open('x', 'X', self.root))
            self.assertFalse(drv.send({'session': 's', 'window': '@1'}, 'hi\n'))
            self.assertFalse(drv.exists({'session': 's', 'window': '@1'}))
            self.assertIsNone(drv.tty({'session': 's', 'window': '@1'}))


class Programa(Fixture):
    TREE = '{"windows": [{"workspaces": [{"ref": "workspace:6", "panes": [{"ref": "pane:2", "surfaces": [{"ref": "surface:9", "type": "terminal", "tty": "ttys004"}]}]}]}]}'

    def test_open_records_the_workspace_and_its_terminal_surface(self):
        drv = terminal.Programa({}, self.root)
        outputs = ['OK workspace:6', self.TREE]
        with patch.object(terminal.subprocess, 'run', side_effect=lambda args, **kw: SimpleNamespace(returncode=0, stdout=outputs.pop(0), stderr='')):
            h = drv.open('backend', 'Backend', self.repo, 'server side')
        self.assertEqual(h, {'workspace': 'workspace:6', 'surface': 'surface:9'})
        with patch.object(terminal.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=self.TREE, stderr='')):
            self.assertTrue(drv.exists(h))
            with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': 'surface:1', 'PROGRAMA_SOCKET_PATH': '/tmp/s'}):
                self.assertEqual(drv.tty(h), 'ttys004')
            with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': '', 'PROGRAMA_SOCKET_PATH': ''}):
                self.assertIsNone(drv.tty(h))                       # not reachable from here: no liveness claim


class Warp(Fixture):
    def setUp(self):
        super().setUp()
        self.tabs = self.root / 'tab_configs'
        patcher = patch.object(terminal, 'WARP_TABS', self.tabs)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.drv = terminal.Warp({}, self.root / 'my Project' / '.teams')

    def test_available_only_inside_warp(self):
        with patch.dict(os.environ, {'TERM_PROGRAM': 'WarpTerminal'}):
            self.assertTrue(self.drv.available())
        with patch.dict(os.environ, {'TERM_PROGRAM': 'iTerm.app'}):
            self.assertFalse(self.drv.available())

    def test_open_writes_the_tab_config_and_asks_warp_to_open_it(self):
        recorded = []
        with patch.object(terminal.subprocess, 'run', side_effect=lambda args, **kw: recorded.append(args) or SimpleNamespace(returncode=0, stdout='', stderr='')), \
             patch.object(terminal.time, 'sleep'):
            h = self.drv.open('backend', 'Back "end"', self.repo, 'server side', command='teams _run backend')
        self.assertEqual(h, {'stem': 'teams-my-project-backend', 'name': 'backend'})
        self.assertEqual(recorded, [['open', 'warp://tab_config/teams-my-project-backend']])
        toml = (self.tabs / 'teams-my-project-backend.toml').read_text()
        self.assertIn('title = "Back \\"end\\""', toml)                  # quotes escaped, not dropped
        self.assertIn(f'directory = "{self.repo}"', toml)
        self.assertIn('commands = ["teams _run backend"]', toml)

    def test_open_needs_a_command_and_survives_a_failing_open(self):
        self.assertIsNone(self.drv.open('backend', 'Backend', self.repo))          # nothing to type later
        self.assertFalse(self.tabs.exists())
        with patch.object(terminal.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='', stderr='')), \
             patch.object(terminal.time, 'sleep'):
            self.assertIsNone(self.drv.open('backend', 'Backend', self.repo, command='teams _run backend'))
        self.assertFalse((self.tabs / 'teams-my-project-backend.toml').exists())   # no tab, no leftover config
        self.assertFalse(self.drv.send({'stem': 's', 'name': 'backend'}, 'hello\n'))
        self.assertIn('Tabs opened in the active Warp window', self.drv.attach_hint())
        self.assertIn('New group with tabs', self.drv.attach_hint())         # `up` prints it as the closing hint

    def pidfile(self, runner=4242, shell=99, started='Wed 17 Sep 10:00:00 2026'):
        f = terminal.pid_file(self.drv.root, 'backend')
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f'{runner}\n{shell} {started}\n')
        return f

    def test_exists_and_tty_read_the_pid_recorded_by_run(self):
        h = {'stem': 'teams-my-project-backend', 'name': 'backend'}
        self.assertFalse(self.drv.exists(h))                                       # no pid file yet
        self.pidfile()
        ps = {'command=': '/usr/local/bin/claude -n backend', 'tty=': 'ttys006'}
        with patch.object(terminal.os, 'kill'), \
             patch.object(terminal.subprocess, 'run', side_effect=lambda args, **kw: SimpleNamespace(returncode=0, stdout=ps[args[2]], stderr='')):
            self.assertTrue(self.drv.exists(h))
            self.assertEqual(self.drv.tty(h), '/dev/ttys006')
            self.assertEqual(self.drv.describe(h), 'warp tab teams-my-project-backend (pid 4242)')
        with patch.object(terminal.os, 'kill', side_effect=OSError('gone')):
            self.assertFalse(self.drv.exists(h))
        ps['command='] = '-zsh'                                                    # pid reused by another process
        with patch.object(terminal.os, 'kill'), \
             patch.object(terminal.subprocess, 'run', side_effect=lambda args, **kw: SimpleNamespace(returncode=0, stdout=ps[args[2]], stderr='')):
            self.assertFalse(self.drv.exists(h))

    def test_wait_ready_returns_as_soon_as_the_tab_reported_its_pid(self):
        h = {'stem': 'teams-my-project-backend', 'name': 'backend'}
        with patch.object(terminal.time, 'sleep') as slept:
            self.drv.wait_ready(h, timeout=0.3)                                    # never written: gives up silently
        self.assertTrue(slept.called)
        self.pidfile()
        with patch.object(terminal.time, 'sleep') as slept:
            self.drv.wait_ready(h, timeout=5)
        self.assertFalse(slept.called)

    def test_close_kills_the_session_hangs_up_the_shell_and_removes_the_files(self):
        h = {'stem': 'teams-my-project-backend', 'name': 'backend'}
        started = 'Wed 17 Sep 10:00:00 2026'
        pidf = self.pidfile(started=started)
        self.tabs.mkdir(parents=True, exist_ok=True)
        (self.tabs / 'teams-my-project-backend.toml').write_text('name = "Backend"\n')
        signals = []
        def kill(pid, sig):
            signals.append((pid, sig))
            if sig == 0:
                raise OSError('gone')                                              # SIGTERM was enough
        with patch.object(terminal.os, 'kill', side_effect=kill), \
             patch.object(terminal.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=started, stderr='')), \
             patch.object(terminal.time, 'sleep'):
            self.drv.close(h)
        self.assertEqual(signals, [(4242, terminal.signal.SIGTERM), (4242, 0), (99, terminal.signal.SIGHUP)])
        self.assertFalse(pidf.exists())
        self.assertFalse((self.tabs / 'teams-my-project-backend.toml').exists())

    def test_close_ignores_a_shell_pid_that_was_reused(self):
        h = {'stem': 'teams-my-project-backend', 'name': 'backend'}
        self.pidfile(started='Wed 17 Sep 10:00:00 2026')
        signals = []
        def kill(pid, sig):
            signals.append((pid, sig))
            raise OSError('gone')
        with patch.object(terminal.os, 'kill', side_effect=kill), \
             patch.object(terminal.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='Thu 18 Sep 08:00:00 2026', stderr='')), \
             patch.object(terminal.time, 'sleep'):
            self.drv.close(h)
        self.assertEqual(signals, [(4242, terminal.signal.SIGTERM)])               # the shell pid is another process now

    def test_record_run_writes_the_runner_and_its_shell(self):
        with patch.object(terminal.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='Wed 17 Sep 10:00:00 2026', stderr='')):
            terminal.record_run(self.drv.root, 'backend')
        lines = terminal.pid_file(self.drv.root, 'backend').read_text().splitlines()
        self.assertEqual(lines[0], str(os.getpid()))
        self.assertEqual(lines[1], f'{os.getppid()} Wed 17 Sep 10:00:00 2026')


import unittest


class TmuxStaleHandles(unittest.TestCase):
    """Window ids are server-wide and reused after a server restart: a handle must only match a
    window of its own session, or `resume` types into another instance's lead."""
    def setUp(self):
        self.calls = []
        self.drv = terminal.Tmux({'tmux_session': 'teams-a'}, '/x')

    def _fake(self, answers):
        def _cmd(*args, timeout=10):
            self.calls.append(args)
            return answers(args)
        self.drv._cmd = _cmd

    def test_exists_is_scoped_to_the_session(self):
        self._fake(lambda a: '@0\n@1' if a[:3] == ('list-windows', '-t', '=teams-a') else None)
        self.assertTrue(self.drv.exists({'session': 'teams-a', 'window': '@1'}))
        self.assertFalse(self.drv.exists({'session': 'teams-a', 'window': '@7'}))
        self.assertIn(('list-windows', '-t', '=teams-a', '-F', '#{window_id}'), self.calls)

    def test_tty_answers_nothing_for_a_window_outside_the_session(self):
        self._fake(lambda a: '' if a[0] == 'list-windows' else '/dev/ttys009')
        self.assertIsNone(self.drv.tty({'session': 'teams-a', 'window': '@0'}))
        self.assertNotIn('display-message', [a[0] for a in self.calls])


class TmuxStatusBar(unittest.TestCase):
    def test_show_puts_the_text_in_the_session_status_bar(self):
        drv = terminal.Tmux({'tmux_session': 'teams-a'}, '/x')
        calls = []
        drv._cmd = lambda *a, timeout=10: calls.append(a) or ''
        drv.show('board http://127.0.0.1:1234')
        self.assertIn(('set-option', '-t', 'teams-a', 'status-right', 'board http://127.0.0.1:1234'), calls)
        self.assertEqual(terminal.Driver({}, '/x').show('anything'), None)   # base: nowhere to put it

    def test_title_is_pushed_to_the_attached_terminal(self):
        drv = terminal.Tmux({'tmux_session': 'teams-a'}, '/x')
        calls = []
        drv._cmd = lambda *a, timeout=10: calls.append(a) or ''
        drv.title('Acme - Manager')
        self.assertIn(('set-option', '-t', 'teams-a', 'set-titles', 'on'), calls)
        self.assertIn(('set-option', '-t', 'teams-a', 'set-titles-string', 'Acme - Manager'), calls)
        self.assertEqual(terminal.Driver({}, '/x').title('anything'), None)
