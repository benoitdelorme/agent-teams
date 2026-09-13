"""Temporary fixtures for local coordination tests."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bin'))
import tasklib
import hooklib
import storage
import terminal


class FakeDriver(terminal.Driver):
    """Records what the launcher asks of a terminal; every operation succeeds."""
    name = 'fake'
    board_in_terminal = False

    def __init__(self, cfg=None, root=None):
        super().__init__(cfg or {}, root or '.')
        self.opened, self.sent, self.closed, self.selected = [], [], [], []
        self.existing = set()

    def available(self):
        return True

    def open(self, name, title, cwd, purpose=''):
        h = {'win': f'win:{len(self.opened) + 1}'}
        self.opened.append((name, h))
        self.existing.add(h['win'])
        return h

    def exists(self, handle):
        return handle['win'] in self.existing

    def send(self, handle, text):
        self.sent.append((handle['win'], text))
        return True

    def close(self, handle):
        self.closed.append(handle['win'])

    def select(self, handle):
        self.selected.append(handle['win'])

    def describe(self, handle):
        return handle['win']


def module(name, filename):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / 'bin' / filename))
    result = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(result)
    return result


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='teams-test-')
        self.root = Path(self.temp.name)
        self.shared = self.root / 'shared'
        self.repo = self.root / 'app'
        self.repo.mkdir()
        self.shared.mkdir()
        self.cfg = {'_root': self.root, '_path': self.root / 'teams.json', 'shared_abs': self.shared,
            'shared_dir': 'shared', 'teams': [
                {'name': 'manager', 'primary': True, 'cwd_abs': self.root},
                {'name': 'backend', 'cwd_abs': self.repo, 'runner': {'command': 'claude'}}]}
        storage.write_json(self.cfg['_path'], {'teams': [{'name': 'manager', 'primary': True}, {'name': 'backend'}],
                                               'session_prefix': 'demo', 'shared_dir': 'shared'})
        self.identity = patch.dict(os.environ, {'TEAMS_TEAM': 'human'})
        self.identity.start()
        self.addCleanup(self.identity.stop)
        self.addCleanup(self.temp.cleanup)

    def task(self, **overrides):
        return tasklib.create(self.shared, 'A task', team='backend', status='todo',
                             criteria='value is two', scope='app.py',
                             verify='python3 -B -c "from app import value; assert value == 2"', **overrides)

    def doing(self, **overrides):
        ticket = self.task(**overrides)
        tasklib.apply_message(self.shared, 'manager', 'backend', f'TASK {ticket["id"]} | implement', event_id='dispatch')
        return ticket['id']
