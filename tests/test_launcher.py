from support import Fixture, module, ROOT
from types import SimpleNamespace
from unittest.mock import patch
import json, shutil, subprocess
import storage
import hooklib

class Launcher(Fixture):
    def test_resume_uses_current_ids_and_starts_missing_teams_fresh(self):
        launcher = module('resume_test', 'teams')
        launcher.STATE = self.root / '.state/surfaces.json'
        launcher.SESS = self.root / '.state/sessions'
        state = {'surfaces': {'gestion': 'surface:1', 'backend': 'surface:2'},
                 'workspaces': {'gestion': 'workspace:1', 'backend': 'workspace:2'}}
        storage.write_json(launcher.STATE, state)
        storage.write_json(launcher.SESS / 'gestion.json', {'session_id': 'recorded-id'})
        with patch.object(launcher, 'workspace_exists', return_value=True), \
             patch.object(launcher, 'process_alive', return_value=False), \
             patch.object(launcher, 'claude_cmd', side_effect=lambda cfg, team, surfaces: ['claude', '-n', team['name']]), \
             patch.object(launcher, 'wait_shell'), patch.object(launcher, 'start_board'), \
             patch.object(launcher, 'programa') as programa:
            launcher.cmd_resume(self.cfg, self.cfg['teams'], self.cfg['teams'][0])
        commands = [c.args[-1] for c in programa.call_args_list if c.args[0] == 'send']
        self.assertEqual(commands, ['claude -n gestion --resume recorded-id\n', 'claude -n backend\n'])

    def test_fresh_up_clears_current_sessions_before_launching(self):
        launcher = module('up_test', 'teams')
        launcher.STATE = self.root / '.state/surfaces.json'
        launcher.SESS = self.root / '.state/sessions'
        storage.write_json(launcher.SESS / 'gestion.json', {'session_id': 'old', 'sessions': ['old']})
        def build(cfg, team, surfaces):
            self.assertEqual(launcher.session_info(team['name']), {})
            return ['claude', '-n', team['name']]
        with patch.object(launcher, 'in_programa', return_value=True), \
             patch.object(launcher, 'pretrust'), patch.object(launcher, 'check_rules_fresh'), \
             patch.object(launcher, 'preflight_runners'), patch.object(launcher, 'wait_shell'), \
             patch.object(launcher, 'workspace_surface', return_value='surface:1'), \
             patch.object(launcher, 'programa', return_value='OK workspace:1'), \
             patch.object(launcher, 'claude_cmd', side_effect=build), patch.object(launcher, 'start_board'):
            launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=False, resume=False))
        self.assertTrue(hooklib.run_id(self.root))
        self.assertTrue(list((self.root / '.state/history').glob('*/sessions/gestion.json')))

    def test_dry_run_preserves_session_state(self):
        launcher = module('dry_run_test', 'teams')
        launcher.STATE = self.root / '.state/surfaces.json'
        launcher.SESS = self.root / '.state/sessions'
        storage.write_json(launcher.SESS / 'gestion.json', {'session_id': 'current'})
        with patch.object(launcher, 'pretrust') as trust, patch.object(launcher, 'check_rules_fresh'), \
             patch.object(launcher, 'claude_cmd', return_value=['claude']):
            launcher.cmd_up(self.cfg, SimpleNamespace(dry_run=True, resume=False))
            self.assertEqual(trust.call_count, 0)
        self.assertEqual(launcher.session_info('gestion')['session_id'], 'current')

    def test_learning_digest_is_reused_when_sources_are_unchanged(self):
        launcher = module('learning_run', 'teams')
        launcher.RULES = self.root / 'rules'
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
        launcher = module('launcher_test', 'teams')
        for directory in ('prompts', 'agents'):
            shutil.copytree(ROOT / directory, self.root / directory)
        cfg = json.loads((ROOT / 'teams.json').read_text())
        for team in cfg['teams']:
            team['cwd'] = '.'
            team['add_dirs'] = []
        storage.write_json(self.cfg['_path'], cfg)
        parsed = launcher.load(self.cfg['_path'])
        command = launcher.claude_cmd(parsed, parsed['teams'][0], {})
        self.assertIn('TEAMS_TEAM=gestion', command)
        self.assertIn('--agents', command)
        self.assertEqual(command[command.index('--model') + 1], 'claude-fable-5-1')
        prompt = (self.root / '.state/prompt-gestion.md').read_text()
        self.assertNotIn('{{', prompt)
        self.assertIn('Agent tool', prompt)
        hooks = json.loads(command[command.index('--settings') + 1])['hooks']
        self.assertIn('PostToolUseFailure', hooks)
