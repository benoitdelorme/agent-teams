from support import Fixture, FakeDriver, module, ROOT
from types import SimpleNamespace
from unittest.mock import patch
import json, os, shutil, subprocess
import storage
import hooklib

class Launcher(Fixture):
    def setUp(self):
        super().setUp()
        self.launcher = module('launcher_' + self._testMethodName, 'teams')
        self.launcher.STATE = self.root / '.state/terminal.json'
        self.launcher.SESS = self.root / '.state/sessions'
        self.launcher.RULES = self.root / 'rules'
        self.launcher.BOARD_STATE = self.root / '.state/board.json'
        self.launcher.BOARD_WS = self.root / '.state/board-tab.json'
        self.driver = FakeDriver()
        patcher = patch.object(self.launcher, 'driver_for', return_value=self.driver)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_resume_uses_current_ids_and_starts_missing_teams_fresh(self):
        launcher = self.launcher
        self.driver.existing.update({'win:1', 'win:2'})
        storage.write_json(launcher.STATE, {'driver': 'fake', 'handles': {'manager': {'win': 'win:1'}, 'backend': {'win': 'win:2'}}})
        storage.write_json(launcher.SESS / 'manager.json', {'session_id': 'recorded-id'})
        with patch.object(launcher, 'process_alive', return_value=False), \
             patch.object(launcher, 'claude_cmd', side_effect=lambda cfg, team: ['claude', '-n', team['name']]), \
             patch.object(launcher, 'start_board'):
            launcher.cmd_resume(self.cfg, self.cfg['teams'], self.cfg['teams'][0])
        self.assertEqual(self.driver.sent, [('win:1', 'claude -n manager --resume recorded-id\n'), ('win:2', 'claude -n backend\n')])
        self.assertEqual(self.driver.opened, [])
        self.assertEqual(self.driver.selected, ['win:1'])

    def test_resume_stops_when_a_terminal_cannot_be_typed_into(self):
        launcher = self.launcher
        self.driver.existing.add('win:1')
        self.driver.send = lambda handle, text: False
        storage.write_json(launcher.STATE, {'driver': 'fake', 'handles': {'manager': {'win': 'win:1'}, 'backend': {'win': 'win:1'}}})
        with patch.object(launcher, 'process_alive', return_value=False), patch.object(launcher, 'start_board'), \
             patch.object(launcher, 'claude_cmd', return_value=['claude']):
            with self.assertRaises(SystemExit):
                launcher.cmd_resume(self.cfg, self.cfg['teams'], self.cfg['teams'][0])

    def test_resume_recreates_a_missing_terminal(self):
        launcher = self.launcher
        self.driver.existing.add('win:9')
        storage.write_json(launcher.STATE, {'driver': 'fake', 'handles': {'manager': {'win': 'win:9'}, 'backend': {'win': 'gone'}}})
        with patch.object(launcher, 'process_alive', return_value=True), patch.object(launcher, 'start_board'):
            launcher.cmd_resume(self.cfg, self.cfg['teams'], self.cfg['teams'][0])
        self.assertEqual([n for n, _ in self.driver.opened], ['backend'])
        self.assertEqual(storage.read_json(launcher.STATE)['handles']['backend'], {'win': 'win:1'})

    def test_fresh_up_clears_current_sessions_before_launching(self):
        launcher = self.launcher
        storage.write_json(launcher.SESS / 'manager.json', {'session_id': 'old', 'sessions': ['old']})
        def build(cfg, team):
            self.assertEqual(launcher.session_info(team['name']), {})
            return ['claude', '-n', team['name']]
        with patch.object(launcher, 'pretrust'), patch.object(launcher, 'check_rules_fresh'), \
             patch.object(launcher, 'preflight_runners'), \
             patch.object(launcher, 'claude_cmd', side_effect=build), patch.object(launcher, 'start_board'):
            launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=False, resume=False))
        self.assertTrue(hooklib.run_id(self.root))
        self.assertTrue(list((self.root / '.state/history').glob('*/sessions/manager.json')))
        state = storage.read_json(launcher.STATE)
        self.assertEqual(state['driver'], 'fake')
        self.assertEqual(sorted(state['handles']), ['backend', 'manager'])
        # non-primary teams are opened first, the primary last so it ends up selected
        self.assertEqual([n for n, _ in self.driver.opened], ['backend', 'manager'])
        self.assertEqual([t for _, t in self.driver.sent], ['claude -n backend\n', 'claude -n manager\n'])
        self.assertEqual(self.driver.selected, ['win:2'])

    def test_down_exits_and_closes_every_terminal(self):
        launcher = self.launcher
        storage.write_json(launcher.STATE, {'driver': 'fake', 'handles': {'manager': {'win': 'win:1'}, 'backend': {'win': 'win:2'}}})
        with patch.object(launcher, 'stop_board'):
            launcher.cmd_down(self.cfg, SimpleNamespace())
        self.assertEqual(self.driver.sent, [('win:1', '/exit\n'), ('win:2', '/exit\n')])
        self.assertEqual(sorted(self.driver.closed), ['win:1', 'win:2'])
        self.assertFalse(launcher.STATE.exists())

    def test_manual_driver_records_the_run_and_refuses_a_second_up(self):
        launcher = self.launcher
        self.driver.name = 'manual'
        with patch.object(launcher, 'pretrust'), patch.object(launcher, 'check_rules_fresh'), \
             patch.object(launcher, 'preflight_runners'), patch.object(launcher, 'start_board'), \
             patch.object(launcher, 'claude_cmd', return_value=['claude']):
            launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=False, resume=False))
            first_run = hooklib.run_id(self.root)
            with self.assertRaises(SystemExit):
                launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=False, resume=False))
        self.assertEqual(storage.read_json(launcher.STATE)['driver'], 'manual')
        self.assertEqual(hooklib.run_id(self.root), first_run)
        self.assertEqual(self.driver.opened, [])

    def test_msg_types_into_the_recorded_terminal(self):
        launcher = self.launcher
        with self.assertRaises(SystemExit):                       # nothing recorded yet
            launcher.cmd_msg(self.cfg, SimpleNamespace(team='backend', text=['hello']))
        storage.write_json(launcher.STATE, {'driver': 'fake', 'handles': {'backend': {'win': 'win:2'}}})
        launcher.cmd_msg(self.cfg, SimpleNamespace(team='backend', text=['hello', 'world']))
        self.assertEqual(self.driver.sent, [('win:2', 'hello world\n')])
        self.driver.send = lambda handle, text: False
        with self.assertRaises(SystemExit):
            launcher.cmd_msg(self.cfg, SimpleNamespace(team='backend', text=['again']))

    def test_status_reports_down_then_liveness_from_the_hooks(self):
        import io, contextlib
        launcher = self.launcher
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            launcher.cmd_status(self.cfg, SimpleNamespace())
        self.assertIn('down (no state)', out.getvalue())
        storage.write_json(launcher.STATE, {'driver': 'manual', 'handles': {}, 'started_at': 'now'})
        storage.write_json(launcher.SESS / 'backend.json', {'status': 'working', 'updated': '2026-09-13T10:00:00', 'session_id': 'abc'})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            launcher.cmd_status(self.cfg, SimpleNamespace())
        lines = out.getvalue().splitlines()
        self.assertTrue(any(l.startswith('  backend') and 'working' in l for l in lines), lines)
        self.assertTrue(any(l.startswith('  manager') and 'DEAD' in l for l in lines), lines)   # no hook record → dead

    def test_config_discovery_walks_up_and_honours_the_environment(self):
        launcher = self.launcher
        project = self.root.resolve() / 'proj'
        (project / 'a' / 'b').mkdir(parents=True)
        (project / '.teams').mkdir()
        storage.write_json(project / '.teams' / 'teams.json', {})
        with patch.object(launcher.Path, 'cwd', return_value=project / 'a' / 'b'), patch.dict(os.environ, {'TEAMS_CONFIG': ''}):
            self.assertEqual(launcher.find_config(), project / '.teams' / 'teams.json')
        with patch.object(launcher.Path, 'cwd', return_value=project / 'a' / 'b'), patch.dict(os.environ, {'TEAMS_CONFIG': '/x/teams.json'}):
            self.assertEqual(launcher.find_config(), launcher.Path('/x/teams.json'))
        import tempfile
        with tempfile.TemporaryDirectory() as lonely:              # the fixture root itself holds a teams.json
            with patch.object(launcher.Path, 'cwd', return_value=launcher.Path(lonely)), patch.dict(os.environ, {'TEAMS_CONFIG': ''}):
                with self.assertRaises(SystemExit):
                    launcher.find_config()

    def test_vendored_engine_takes_over(self):
        launcher = self.launcher
        inst = self.root.resolve() / '.teams'
        (inst / 'engine' / 'bin').mkdir(parents=True)
        (inst / 'engine' / 'bin' / 'teams').write_text('#!/usr/bin/env python3\n')
        storage.write_json(inst / 'teams.json', {'teams': []})
        with patch.object(launcher.sys, 'argv', ['teams', '--config', str(inst / 'teams.json'), 'status']), \
             patch.object(launcher.os, 'execv', side_effect=RuntimeError('exec')) as execv:
            with self.assertRaises(RuntimeError):
                launcher.main()
        argv = execv.call_args.args[1]
        self.assertEqual(argv[1:], [str(inst / 'engine' / 'bin' / 'teams'), '--config', str(inst / 'teams.json'), 'status'])

    def test_dry_run_preserves_session_state(self):
        launcher = self.launcher
        storage.write_json(launcher.SESS / 'manager.json', {'session_id': 'current'})
        with patch.object(launcher, 'pretrust') as trust, patch.object(launcher, 'check_rules_fresh'), \
             patch.object(launcher, 'claude_cmd', return_value=['claude']):
            launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=True, resume=False))
            self.assertEqual(trust.call_count, 0)
        self.assertEqual(launcher.session_info('manager')['session_id'], 'current')
        self.assertEqual(self.driver.opened, [])

    def test_learning_digest_is_reused_when_sources_are_unchanged(self):
        launcher = self.launcher
        (self.repo / 'README.md').write_text('Python repo. Test: python3 -m unittest')
        args = SimpleNamespace(team='backend', force=False, dry_run=False, model='fake')
        response = subprocess.CompletedProcess([], 0, 'STACK: Python\nCOMMANDS:\n- test: python3 -m unittest', '')
        with patch.object(launcher.subprocess, 'run', return_value=response) as call:
            launcher.cmd_learn(self.cfg, args)
            self.assertEqual(call.call_count, 1)
        self.assertIn('STACK: Python', launcher.rules_digest('backend'))
        with patch.object(launcher.subprocess, 'run') as call:
            launcher.cmd_learn(self.cfg, args)
            call.assert_not_called()


    def test_generated_commands_register_native_workers(self):
        launcher = self.launcher
        # an instance holds only teams.json: prompts and workers resolve to the engine defaults
        cfg = json.loads((ROOT / 'examples/demo/.teams/teams.json').read_text())
        cfg['language'] = 'French'
        for team in cfg['teams']:
            team['cwd'] = '.'
            team['add_dirs'] = []
        storage.write_json(self.cfg['_path'], cfg)
        parsed = launcher.load(self.cfg['_path'])
        with patch.object(launcher.shutil, 'which', return_value=None):
            command = launcher.claude_cmd(parsed, parsed['teams'][0])
        self.assertIn('TEAMS_TEAM=manager', command)
        workers = json.loads((self.root / '.state/workers-manager.json').read_text())
        self.assertEqual({k: v['model'] for k, v in workers.items()}, {'worker-simple': 'claude-sonnet-5', 'worker-complex': 'claude-opus-5'})
        self.assertNotIn('{{', workers['worker-simple']['prompt'])
        self.assertIn('--agents', command)
        self.assertEqual(command[command.index('--model') + 1], 'claude-fable-5-1')
        prompt = (self.root / '.state/prompt-manager.md').read_text()
        self.assertNotIn('{{', prompt)
        self.assertIn('Agent tool', prompt)
        self.assertIn('Talk to the human in French', prompt)
        self.assertIn(f'{launcher.SELF} task new', prompt)          # `teams` not on PATH: prompts carry the explicit path
        hooks = json.loads(command[command.index('--settings') + 1])['hooks']
        self.assertIn('PostToolUseFailure', hooks)

    def test_instance_prompt_overrides_engine_default(self):
        launcher = self.launcher
        cfg = json.loads((ROOT / 'examples/demo/.teams/teams.json').read_text())
        for team in cfg['teams']:
            team['cwd'] = '.'
            team['add_dirs'] = []
        storage.write_json(self.cfg['_path'], cfg)
        (self.root / 'prompts').mkdir()
        (self.root / 'prompts/backend.md').write_text('# Role: CUSTOM BACKEND for {{team}}')
        parsed = launcher.load(self.cfg['_path'])
        launcher.claude_cmd(parsed, parsed['teams'][1])
        prompt = (self.root / '.state/prompt-backend.md').read_text()
        self.assertIn('CUSTOM BACKEND for backend', prompt)
        self.assertIn('# Inter-team communication protocol', prompt)

    def test_init_scaffolds_an_instance(self):
        launcher = self.launcher
        (self.repo / 'package.json').write_text(json.dumps({'dependencies': {'react': '19'}}))
        inst = self.root / 'teams'
        launcher.cmd_init(SimpleNamespace(dir=str(inst), repo=[str(self.repo)], force=False, language='English'))
        cfg = json.loads((inst / 'teams.json').read_text())
        self.assertEqual([t['name'] for t in cfg['teams']], ['manager', 'frontend'])
        self.assertEqual(cfg['teams'][1]['cwd'], '../app')
        self.assertTrue((inst / 'prompts/manager.md').is_file())
        self.assertTrue((inst / '.gitignore').is_file())
        self.assertFalse((inst / 'teams').exists())
        self.assertEqual(json.loads((inst / 'teams.json').read_text())['engine_version'], launcher.VERSION)
        with self.assertRaises(SystemExit):
            launcher.cmd_init(SimpleNamespace(dir=str(inst), repo=[str(self.repo)], force=False, language='English'))

    def test_init_without_any_app_creates_a_dev_team(self):
        launcher = self.launcher
        inst = self.root / 'empty' / '.teams'
        (self.root / 'empty').mkdir()
        launcher.cmd_init(SimpleNamespace(dir=str(inst), repo=[], force=False, language='English'))
        cfg = json.loads((inst / 'teams.json').read_text())
        self.assertEqual([t['name'] for t in cfg['teams']], ['manager', 'dev'])
        self.assertEqual(cfg['teams'][1]['cwd'], '..')
        self.assertIn('# Role: DEV team', (inst / 'prompts/dev.md').read_text())
        self.assertEqual(cfg['terminal'], 'auto')
