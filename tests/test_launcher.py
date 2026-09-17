from support import Fixture, FakeDriver, module, ROOT
from types import SimpleNamespace
from unittest.mock import patch
import json, os, shutil, subprocess
import storage
import hooklib

class LauncherCase(Fixture):
    """bin/teams loaded as a module, its instance paths under the fixture root, a fake driver."""

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


class Launcher(LauncherCase):
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

    def test_session_prefix_names_sessions_and_roster(self):
        for t in self.cfg['teams']:
            t.setdefault('runner', {'command': 'claude'})
        self.cfg.setdefault('defaults', {})
        self.assertEqual(self.launcher.session_name(self.cfg, 'backend'), 'backend')
        self.cfg['session_prefix'] = 'demo'
        self.assertEqual(self.launcher.session_name(self.cfg, 'backend'), 'demo-backend')
        roster = self.launcher.roster_text(self.cfg, self.cfg['teams'][0])
        self.assertIn('session=demo-backend', roster)
        self.assertIn('session=demo-manager', roster)
        self.assertIn('never the bare team name', roster)
        del self.cfg['session_prefix']
        self.assertNotIn('session=', self.launcher.roster_text(self.cfg, self.cfg['teams'][0]))

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

    def test_relay_writes_each_live_team_state_into_its_own_terminal(self):
        """What the leads emitted before anyone attached is lost: an attach replays it per terminal."""
        launcher = self.launcher
        ttys = {name: self.root / f'tty-{name}' for name in ('manager', 'backend')}
        for path in ttys.values():
            path.write_text('')
        storage.write_json(launcher.STATE, {'driver': 'fake', 'handles': {
            'manager': {'win': 'win:1'}, 'backend': {'win': 'win:2'}}})
        storage.write_json(launcher.SESS / 'manager.json', {'session_id': 'm1', 'cwd': str(self.root), 'status': 'working'})
        storage.write_json(launcher.SESS / 'backend.json', {'session_id': 'b1', 'cwd': str(self.repo), 'status': 'gone'})
        self.driver.session_environ = lambda: {'TEAMS_HOST_TERM_PROGRAM': 'WarpTerminal',
                                               'TEAMS_HOST_WARP_CLI_AGENT_PROTOCOL_VERSION': '1'}
        self.driver.tty = lambda handle: str(ttys['manager' if handle['win'] == 'win:1' else 'backend'])
        launcher.cmd_relay(self.cfg, SimpleNamespace())
        written = ttys['manager'].read_text()
        self.assertEqual(written.count('\x1bPtmux;'), 2)              # session_start, then the current state
        self.assertIn('"event":"session_start"', written)
        self.assertIn('"event":"prompt_submit"', written)
        self.assertIn('"session_id":"m1"', written)
        self.assertEqual(ttys['backend'].read_text(), '')              # gone: nothing to show
        # a team whose terminal has no tty is skipped, and a missing device is not an error
        ttys['manager'].write_text('')
        self.driver.tty = lambda handle: None
        launcher.cmd_relay(self.cfg, SimpleNamespace())
        self.assertEqual(ttys['manager'].read_text(), '')
        self.driver.tty = lambda handle: str(self.root / 'no-such-device')
        launcher.cmd_relay(self.cfg, SimpleNamespace())                # writes a file here, never raises

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
        launcher.cmd_init(SimpleNamespace(dir=str(inst), repo=[str(self.repo)], force=False, language='English', no_ai=True, yes=True, dry_run=False, model='fake'))
        cfg = json.loads((inst / 'teams.json').read_text())
        self.assertEqual([t['name'] for t in cfg['teams']], ['manager', 'frontend'])
        self.assertEqual(cfg['teams'][1]['cwd'], '../app')
        self.assertTrue((inst / 'prompts/manager.md').is_file())
        self.assertTrue((inst / '.gitignore').is_file())
        self.assertFalse((inst / 'teams').exists())
        self.assertEqual(json.loads((inst / 'teams.json').read_text())['engine_version'], launcher.VERSION)
        with self.assertRaises(SystemExit):
            launcher.cmd_init(SimpleNamespace(dir=str(inst), repo=[str(self.repo)], force=False, language='English', no_ai=True, yes=True, dry_run=False, model='fake'))

    def test_init_without_any_app_creates_a_dev_team(self):
        launcher = self.launcher
        inst = self.root / 'empty' / '.teams'
        (self.root / 'empty').mkdir()
        launcher.cmd_init(SimpleNamespace(dir=str(inst), repo=[], force=False, language='English', no_ai=True, yes=True, dry_run=False, model='fake'))
        cfg = json.loads((inst / 'teams.json').read_text())
        self.assertEqual([t['name'] for t in cfg['teams']], ['manager', 'dev'])
        self.assertEqual(cfg['teams'][1]['cwd'], '..')
        self.assertIn('# Role: DEV team', (inst / 'prompts/dev.md').read_text())
        self.assertEqual(cfg['terminal'], 'auto')

    PROPOSAL = json.dumps({
        "project": "A shop: web app and API",
        "teams": [
            {"name": "backend", "kind": "backend", "cwd": "api", "stack": "FastAPI, uv", "purpose": "Owns the API",
             "scope": "Everything under api/, never the web app", "verify": ["uv run pytest"], "talks_to": ["frontend"],
             "evidence": "web/vite.config.ts proxies /api to :8010 served by api/"},
            {"name": "frontend", "kind": "frontend", "cwd": "web", "stack": "React, Vite, pnpm", "purpose": "Owns the web app",
             "scope": "", "verify": ["pnpm build", "pnpm lint"], "talks_to": ["backend"], "evidence": "web/package.json"},
            {"name": "manager", "kind": "other", "cwd": ".", "purpose": "must be ignored"},
            {"name": "ops", "kind": "infra", "cwd": "../elsewhere", "purpose": "outside the project: dropped"},
            {"name": "docs", "kind": "docs", "cwd": "docs", "purpose": "Keeps the handbook", "verify": [], "talks_to": ["ops", "frontend", "docs"]},
        ],
        "links": ["web/vite.config.ts → api/ on port 8010"],
        "skipped": ["assets/: images only"],
    })

    def init_args(self, inst, **over):
        base = dict(dir=str(inst), repo=[], force=False, language='English', no_ai=False, yes=True, dry_run=False, model='fake')
        return SimpleNamespace(**{**base, **over})

    def shop(self):
        project = self.root / 'shop'
        for d in ('api', 'web', 'docs', 'assets'):
            (project / d).mkdir(parents=True)
        (project / 'api' / 'pyproject.toml').write_text('[project]\nname = "api"\ndependencies = ["fastapi"]\n')
        (project / 'web' / 'package.json').write_text(json.dumps({'dependencies': {'react': '19'}, 'scripts': {'build': 'vite build'}}))
        (project / 'web' / 'vite.config.ts').write_text("export default { server: { proxy: { '/api': 'http://localhost:8010' } } }")
        (project / 'web' / 'node_modules' / 'react').mkdir(parents=True)
        (project / 'web' / 'node_modules' / 'react' / 'package.json').write_text('{}')
        (project / 'docs' / 'handbook.md').write_text('# Handbook')
        return project

    def test_init_snapshot_shows_the_tree_and_the_linking_files_but_not_dependencies(self):
        project = self.shop()
        snap = self.launcher.snapshot_project([project])
        self.assertIn('## TREE', snap)
        self.assertIn('web/vite.config.ts', snap)
        self.assertIn("proxy: { '/api'", snap)            # file content, not only its name
        self.assertNotIn('node_modules', snap)

    def test_init_uses_the_model_proposal_and_asks_nothing_with_yes(self):
        launcher = self.launcher
        project = self.shop()
        inst = project / '.teams'
        sent = {}
        def fake_run(args, **kw):
            sent['prompt'] = kw.get('input', '')
            return subprocess.CompletedProcess(args, 0, self.PROPOSAL, '')
        with patch.object(launcher.subprocess, 'run', side_effect=fake_run):
            launcher.cmd_init(self.init_args(inst))
        self.assertIn('## FILE shop/web/vite.config.ts', sent['prompt'])
        cfg = json.loads((inst / 'teams.json').read_text())
        self.assertEqual([t['name'] for t in cfg['teams']], ['manager', 'backend', 'frontend', 'docs'])
        self.assertEqual({t['name']: t['cwd'] for t in cfg['teams']}, {'manager': '..', 'backend': '../api', 'frontend': '../web', 'docs': '../docs'})
        self.assertEqual(cfg['teams'][1]['purpose'], 'Owns the API')
        self.assertEqual(sorted(cfg['teams'][0]['add_dirs']), ['../api', '../docs', '../web'])
        backend = (inst / 'prompts/backend.md').read_text()
        self.assertIn('# Role: BACKEND team', backend)               # the engine's role for the kind
        self.assertIn('## This project', backend)
        self.assertIn('`uv run pytest`', backend)
        self.assertIn('Interfaces with: frontend', backend)
        docs = (inst / 'prompts/docs.md').read_text()
        self.assertIn('# Role: DOCS team', docs)                     # no engine role for docs: the template
        self.assertIn('Needs frontend for shared interfaces', docs)  # ops was dropped, docs is itself: both filtered out
        self.assertTrue((inst / 'prompts/manager.md').is_file())

    def test_init_falls_back_to_the_manifest_scan_when_the_model_fails(self):
        launcher = self.launcher
        project = self.shop()
        inst = project / '.teams'
        with patch.object(launcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'boom')):
            launcher.cmd_init(self.init_args(inst))
        cfg = json.loads((inst / 'teams.json').read_text())
        self.assertEqual(sorted(t['name'] for t in cfg['teams']), ['backend', 'frontend', 'manager'])

    def test_init_dry_run_shows_the_proposal_and_writes_nothing(self):
        launcher = self.launcher
        project = self.shop()
        inst = project / '.teams'
        import io, contextlib
        out = io.StringIO()
        with patch.object(launcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, self.PROPOSAL, '')), contextlib.redirect_stdout(out):
            launcher.cmd_init(self.init_args(inst, dry_run=True))
        self.assertIn('backend', out.getvalue())
        self.assertIn('web/vite.config.ts → api/ on port 8010', out.getvalue())
        self.assertFalse(inst.exists())

    def test_init_refuses_to_guess_when_not_a_terminal_and_not_yes(self):
        launcher = self.launcher
        project = self.shop()
        with patch.object(launcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, self.PROPOSAL, '')), \
             patch.object(launcher.sys.stdin, 'isatty', return_value=False):
            with self.assertRaises(SystemExit):
                launcher.cmd_init(self.init_args(project / '.teams', yes=False))
        self.assertFalse((project / '.teams').exists())

    def test_parse_proposal_rejects_junk(self):
        launcher = self.launcher
        project = self.shop()
        self.assertIsNone(launcher.parse_proposal('no json here', project))
        self.assertIsNone(launcher.parse_proposal('{"teams": [{"name": "x", "cwd": "../.."}]}', project))
        p = launcher.parse_proposal('```json\n{"teams": [{"name": "Web App!", "cwd": "web"}]}\n```', project)
        self.assertEqual(p['teams'][0]['name'], 'web-app')


class NonTypingDriver(LauncherCase):
    """A terminal the launcher cannot type into (Warp): the command travels with the tab."""

    def setUp(self):
        super().setUp()
        self.driver.types_commands = False
        self.driver.name = 'warp'

    def test_up_hands_the_run_command_to_the_tab_and_never_types(self):
        import io, contextlib
        launcher = self.launcher
        self.driver.attach_hint = lambda: 'these terminals started themselves'
        out = io.StringIO()
        with patch.object(launcher, 'pretrust'), patch.object(launcher, 'check_rules_fresh'), \
             patch.object(launcher, 'preflight_runners'), patch.object(launcher, 'start_board'), \
             patch.object(launcher, 'claude_cmd', return_value=['claude']), contextlib.redirect_stdout(out):
            launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=False, resume=False))
        self.assertEqual(self.driver.sent, [])                       # nothing typed: the terminal runs its own command
        self.assertEqual([n for n, _ in self.driver.commands], ['backend', 'manager'])
        for name, command in self.driver.commands:
            self.assertIn(f'{launcher.SELF}', command)
            self.assertIn(f'_run {name}', command)
        self.assertIn('these terminals started themselves', out.getvalue())   # whatever the driver has to say, verbatim

    def test_msg_refuses_a_terminal_it_cannot_type_into(self):
        import io, contextlib
        launcher = self.launcher
        storage.write_json(launcher.STATE, {'driver': 'warp', 'handles': {'backend': {'win': 'win:2'}}})
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            launcher.cmd_msg(self.cfg, SimpleNamespace(team='backend', text=['hello']))
        self.assertIn('teams msg cannot type into a warp terminal', err.getvalue())
        self.assertEqual(self.driver.sent, [])

    def test_resume_gives_a_dead_team_a_fresh_tab_carrying_its_resume_id(self):
        launcher = self.launcher
        self.driver.existing.update({'win:1', 'win:2'})
        storage.write_json(launcher.STATE, {'driver': 'warp', 'handles': {'manager': {'win': 'win:1'}, 'backend': {'win': 'win:2'}}})
        storage.write_json(launcher.SESS / 'manager.json', {'session_id': 'recorded-id'})
        with patch.object(launcher, 'process_alive', side_effect=lambda cfg, name: name == 'backend'), \
             patch.object(launcher, 'claude_cmd', return_value=['claude']), patch.object(launcher, 'start_board'):
            launcher.cmd_resume(self.cfg, self.cfg['teams'], self.cfg['teams'][0])
        self.assertEqual(self.driver.sent, [])
        self.assertEqual(self.driver.closed, ['win:1'])              # leftovers of the dead session go first
        self.assertEqual([n for n, _ in self.driver.opened], ['manager'])
        self.assertIn('--resume-id recorded-id', self.driver.commands[0][1])
        self.assertEqual(storage.read_json(launcher.STATE)['handles']['manager'], {'win': 'win:1'})

    def test_a_dead_tab_is_dead_whatever_the_hooks_last_recorded(self):
        launcher = self.launcher
        storage.write_json(launcher.STATE, {'driver': 'warp', 'handles': {'backend': {'win': 'win:2'}}})
        storage.write_json(launcher.SESS / 'backend.json', {'session_id': 'x', 'status': 'idle'})
        self.driver.existing.clear()                                 # its session is gone, the tab may not be
        self.assertFalse(launcher.process_alive(self.cfg, 'backend'))
        self.driver.existing.add('win:2')
        self.assertTrue(launcher.process_alive(self.cfg, 'backend'))

    def test_run_records_its_pid_then_execs_claude_with_the_workers_inlined(self):
        launcher = self.launcher
        cfg = json.loads((ROOT / 'examples/demo/.teams/teams.json').read_text())
        for team in cfg['teams']:
            team['cwd'] = '.'
            team['add_dirs'] = []
        storage.write_json(self.cfg['_path'], cfg)
        parsed = launcher.load(self.cfg['_path'])
        with patch.object(launcher.os, 'execvp') as execvp:
            launcher.cmd_run(parsed, SimpleNamespace(team='backend', resume_id='sid-7'))
        binary, argv = execvp.call_args.args
        self.assertEqual(binary, 'claude')
        self.assertEqual(argv[0], 'claude')
        workers = (self.root / '.state/workers-backend.json').read_text()
        self.assertEqual(argv[argv.index('--agents') + 1], workers)   # exec has no shell to expand $(cat …)
        self.assertEqual(argv[-2:], ['--resume', 'sid-7'])
        self.assertEqual(os.environ['TEAMS_TEAM'], 'backend')
        self.assertEqual(os.environ['TEAMS_CONFIG'], str(parsed['_path']))
        pid_file = parsed['_root'] / '.state/runs/backend.pid'
        self.assertEqual(pid_file.read_text().splitlines()[0], str(os.getpid()))
        self.assertTrue(pid_file.read_text().splitlines()[1].startswith(f'{os.getppid()} '))
        self.assertIn('## run backend', (self.shared / 'LOG.md').read_text())
        with patch.object(launcher.os, 'execvp') as execvp:
            launcher.cmd_run(parsed, SimpleNamespace(team='backend', resume_id=None))
        self.assertNotIn('--resume', execvp.call_args.args[1])
        with self.assertRaises(SystemExit):
            launcher.cmd_run(parsed, SimpleNamespace(team='nope', resume_id=None))
