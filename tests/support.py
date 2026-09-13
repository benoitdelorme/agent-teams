"""Temporary fixtures for local coordination tests."""
from concurrent.futures import ThreadPoolExecutor
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bin'))
import tasklib
import hooklib
import storage


def module(name, filename):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / 'bin' / filename))
    result = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(result)
    return result


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='teams-organisation-')
        self.root = Path(self.temp.name)
        self.shared = self.root / 'shared'
        self.repo = self.root / 'app'
        self.repo.mkdir()
        self.shared.mkdir()
        self.cfg = {'_root': self.root, '_path': self.root / 'teams.json', 'shared_abs': self.shared,
            'shared_dir': 'shared', 'teams': [
                {'name': 'gestion', 'primary': True, 'cwd_abs': self.root},
                {'name': 'backend', 'cwd_abs': self.repo, 'runner': {'command': 'claude'}}]}
        storage.write_json(self.cfg['_path'], {'teams': [{'name': 'gestion', 'primary': True}, {'name': 'backend'}],
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
        tasklib.apply_message(self.shared, 'gestion', 'backend', f'TASK {ticket["id"]} | implement', event_id='dispatch')
        return ticket['id']
