from support import Fixture
from unittest.mock import patch
from types import SimpleNamespace
import os
import terminal


class Detect(Fixture):
    def test_auto_prefers_programa_then_tmux_then_manual(self):
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': 'surface:1', 'PROGRAMA_SOCKET_PATH': '/tmp/s'}):
            self.assertEqual(terminal.detect({}, self.root).name, 'programa')
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': '', 'PROGRAMA_SOCKET_PATH': ''}):
            with patch.object(terminal.shutil, 'which', return_value='/usr/bin/tmux'):
                self.assertEqual(terminal.detect({}, self.root).name, 'tmux')
            with patch.object(terminal.shutil, 'which', return_value=None):
                self.assertEqual(terminal.detect({}, self.root).name, 'manual')

    def test_explicit_choice_wins_and_unknown_names_are_rejected(self):
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': 'surface:1', 'PROGRAMA_SOCKET_PATH': '/tmp/s'}):
            self.assertEqual(terminal.detect({'terminal': 'tmux'}, self.root).name, 'tmux')
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
        recorded, patcher = self.calls([None, '@7', '', '@8'])       # has-session fails, new-session, has-session ok, new-window
        with patcher:
            first = drv.open('backend', 'Backend', self.repo)
            second = drv.open('manager', 'Manager', self.root)
        self.assertEqual(first, {'session': 'teams-my-project', 'window': '@7'})
        self.assertEqual(second['window'], '@8')
        self.assertEqual(recorded[1][:5], ['tmux', 'new-session', '-d', '-s', 'teams-my-project'])
        self.assertEqual(recorded[3][:5], ['tmux', 'new-window', '-d', '-t', '=teams-my-project:'])   # exact session, not a prefix
        self.assertEqual(terminal.Tmux({}, self.root / 'flat-project').session, 'teams-flat-project')  # config at the project root

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
