from support import Fixture, FakeDriver, module
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import contextlib, io, json, os, shlex, signal, socket, subprocess, time
import remote
import terminal

TARGET = {'host': 'sky-a', 'path': '~/work/my project'}
LOCAL = ('.teams/teams.json', 'teams/teams.json', 'teams.json')


class Target(Fixture):
    def test_parse_target_needs_host_and_path(self):
        self.assertEqual(remote.parse_target('sky-a:~/work/p'), {'host': 'sky-a', 'path': '~/work/p'})
        self.assertEqual(remote.parse_target('me@10.0.0.2:/srv/p:x'), {'host': 'me@10.0.0.2', 'path': '/srv/p:x'})
        for bad in ('sky-a', 'sky-a:', ':~/p', ''):
            with self.assertRaises(ValueError):
                remote.parse_target(bad)

    def test_find_prefers_the_environment_then_the_nearest_file(self):
        project = self.root.resolve() / 'proj'
        (project / 'a' / 'b').mkdir(parents=True)
        (project / '.teams').mkdir()
        (project / '.teams' / 'remote.json').write_text(json.dumps({'host': 'sky-a', 'path': '~/p', 'mouse': False}))
        with patch.dict(os.environ, {'TEAMS_REMOTE': ''}):
            found = remote.find(project / 'a' / 'b', LOCAL)
        self.assertEqual(found, {'host': 'sky-a', 'path': '~/p', 'mouse': False, '_file': project / '.teams' / 'remote.json'})
        with patch.dict(os.environ, {'TEAMS_REMOTE': 'other:/srv/x'}):
            self.assertEqual(remote.find(project / 'a', LOCAL), {'host': 'other', 'path': '/srv/x'})

    def test_a_nearer_local_instance_wins_and_a_bad_file_is_refused(self):
        project = self.root.resolve() / 'proj'
        (project / 'app' / '.teams').mkdir(parents=True)
        (project / '.teams').mkdir()
        (project / '.teams' / 'remote.json').write_text(json.dumps({'host': 'sky-a', 'path': '~/p'}))
        (project / 'app' / '.teams' / 'teams.json').write_text('{}')
        with patch.dict(os.environ, {'TEAMS_REMOTE': ''}):
            self.assertIsNone(remote.find(project / 'app', LOCAL))
            (project / '.teams' / 'remote.json').write_text(json.dumps({'host': 'sky-a'}))
            with self.assertRaises(ValueError):
                remote.find(project, LOCAL)

    def test_remote_json_beside_a_local_instance_wins(self):
        inst = self.root.resolve() / 'clone' / '.teams'
        inst.mkdir(parents=True)
        (inst / 'teams.json').write_text('{}')
        (inst / 'remote.json').write_text(json.dumps({'host': 'sky-a', 'path': '~/p'}))
        with patch.dict(os.environ, {'TEAMS_REMOTE': ''}):
            self.assertEqual(remote.find(inst.parent, LOCAL)['host'], 'sky-a')


class Relay(Fixture):
    def test_remote_line_runs_teams_in_the_project_through_a_login_shell(self):
        home = self.root.resolve()
        (home / 'work' / 'my project').mkdir(parents=True)
        target = {'host': 'h', 'path': '~/work/my project', 'command': 'pwd && printf "%s\\n"'}
        line = remote.remote_line(target, ['a b', "it's", '$HOME'])
        self.assertTrue(line.startswith('exec "$SHELL" -lc '), line)
        r = subprocess.run(['/bin/sh', '-c', line], capture_output=True, text=True, timeout=10,
                           env={'SHELL': '/bin/sh', 'HOME': str(home), 'PATH': os.environ.get('PATH', '/usr/bin:/bin')})
        self.assertEqual(r.stdout.splitlines(), [str(home / 'work' / 'my project'), 'a b', "it's", '$HOME'])
        self.assertIn('&& teams ', remote.remote_line(TARGET, ['status']))       # the default command

    def test_ssh_argv_places_options_before_the_host(self):
        target = {**TARGET, 'ssh_options': ['-p', '2222']}
        self.assertEqual(remote.ssh_argv(target, 'cmd', tty=True, options=['-N']), ['ssh', '-t', '-N', '-p', '2222', 'sky-a', 'cmd'])
        self.assertEqual(remote.ssh_argv(TARGET), ['ssh', 'sky-a'])

    def test_run_streams_and_returns_the_remote_exit_code(self):
        with patch.object(remote.subprocess, 'call', return_value=3) as call:
            self.assertEqual(remote.run(TARGET, ['down']), 3)
        self.assertEqual(call.call_args.args[0], ['ssh', 'sky-a', remote.remote_line(TARGET, ['down'])])
        with patch.object(remote.subprocess, 'call', side_effect=OSError('no ssh')):
            with self.assertRaises(remote.RemoteError):
                remote.run(TARGET, ['down'])

    def test_relay_hands_the_process_to_ssh_with_a_terminal_only_when_interactive(self):
        for interactive, flag in ((True, ['-t']), (False, [])):
            with patch.object(remote, '_interactive', return_value=interactive), patch.object(remote.os, 'execvp') as execvp:
                remote.relay(TARGET, ['task', 'list'])
            self.assertEqual(execvp.call_args.args, ('ssh', ['ssh', *flag, 'sky-a', remote.remote_line(TARGET, ['task', 'list'])]))

    def test_main_relays_a_command(self):
        with patch.object(remote, 'relay') as relay:
            remote.main(TARGET, SimpleNamespace(cmd='task'), ['task', 'list'])
        relay.assert_called_once_with(TARGET, ['task', 'list'])

    def test_quote_never_leaves_a_word_bare(self):
        self.assertEqual(remote.quote('status'), "'status'")
        self.assertEqual(remote.quote('=ls'), "'=ls'")
        self.assertEqual(remote.quote(''), "''")
        self.assertEqual(remote.quote("it's"), "'it'\"'\"'s'")
        line = remote.remote_line({'host': 'h', 'path': '~/my project'}, ['msg', 'web', '=ls'])
        self.assertEqual(line, 'exec "$SHELL" -lc ' + remote.quote("cd ~/'my project' && teams 'msg' 'web' '=ls'"))


HOSTILE = ['=ls', '==', '=', '=nosuchcmd_zz', '%self', '~', '~root', '*', '?', '$HOME', '`id`', '$(id)', 'a b', "it's", '', '-n', '--',
           '{a,b}', '<1-3>', '!!', '#x', 'a\\b', '\\', 'é', 'a\nb', ';', '|', '&', '>', 'x=y', '[a]', 'a\'b"c', '\t', '=(ls)', '<(ls)']


class Shells(Fixture):
    """The relay line read by real shells acting as the server's login shell: every word arrives as typed."""
    def setUp(self):
        super().setUp()
        self.home = self.root.resolve() / 'home'                  # the remote user's home: no start-up file in it
        for name in ('proj', '=ls', '=x y', '-P'):
            (self.home / name).mkdir(parents=True)
        self.there = self.root.resolve() / 'teams-there'          # stands for `teams` on the server: says where it runs and what it received
        self.there.write_text('#!/bin/sh\nprintf "teams-there\\n"; pwd\nfor word; do printf "%s\\0" "$word"; done\n')
        self.there.chmod(0o755)

    def arrive(self, shell, path, words):
        """The relay line as ssh hands it to `shell`: (the directory the command ran in, the words it received)."""
        target = {'host': 'h', 'path': path, 'command': "'" + str(self.there) + "'"}
        env = {'SHELL': shell, 'HOME': str(self.home), 'ZDOTDIR': str(self.home), 'ENV': '', 'PATH': '/usr/bin:/bin'}
        r = subprocess.run([shell, '-c', remote.remote_line(target, words)], capture_output=True, text=True, timeout=30, env=env, cwd=self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        cwd, _, received = r.stdout.rpartition('teams-there\n')[2].partition('\n')   # a login shell may print before the command does
        return cwd, received.split('\0')[:-1]

    def verbatim(self, name):
        shell = next((p for p in (f'/bin/{name}', f'/usr/bin/{name}', f'/usr/local/bin/{name}', f'/opt/homebrew/bin/{name}') if os.path.exists(p)), None)
        if not shell:
            self.skipTest(f'{name} is not installed here')
        self.assertEqual(self.arrive(shell, str(self.home / 'proj'), ['msg', *HOSTILE])[1], ['msg', *HOSTILE])
        for path, there in (('=ls', self.home / '=ls'), ('~/=x y', self.home / '=x y'), ('-P', self.home / '-P'), ('~', self.home),
                            ('~/proj', self.home / 'proj')):
            with self.subTest(path=path):
                self.assertEqual(self.arrive(shell, path, ['status']), (str(there), ['status']))

    def test_sh(self):
        self.verbatim('sh')

    def test_bash(self):
        self.verbatim('bash')

    def test_zsh(self):
        self.verbatim('zsh')

    def test_dash(self):
        self.verbatim('dash')

    def test_ksh(self):
        self.verbatim('ksh')


class Status(Fixture):
    def answer(self, stdout='', stderr='', code=0):
        return patch.object(remote.subprocess, 'run', return_value=SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr))

    def test_status_reads_the_last_json_line(self):
        with self.answer('Welcome to sky-a\n{"up": false, "teams": []}\n') as run:
            self.assertEqual(remote.status(TARGET), {'up': False, 'teams': []})
        self.assertEqual(run.call_args.args[0], ['ssh', 'sky-a', remote.remote_line(TARGET, ['status', '--json'])])

    def test_status_reads_a_line_holding_unicode_line_separators(self):
        purpose = 'first' + chr(0x2028) + 'second' + chr(0x2029) + 'third' + chr(0x85) + 'end'   # str.splitlines() cuts at each of them
        answer = {'up': True, 'teams': [{'name': 'web', 'purpose': purpose}]}
        with self.answer('Welcome to sky-a\n' + json.dumps(answer, ensure_ascii=False) + '\n'):
            self.assertEqual(remote.status(TARGET), answer)                    # one line of JSON is read as one line

    def test_status_failures_name_the_target_and_hint_an_old_engine(self):
        with self.answer(stderr='teams: no teams.json found here or above\n', code=1):
            with self.assertRaisesRegex(remote.RemoteError, r'^sky-a:~/work/my project: teams: no teams.json'):
                remote.status(TARGET)
        with self.answer(stderr='usage: teams …\nteams: error: unrecognized arguments: --json\n', code=2):
            with self.assertRaisesRegex(remote.RemoteError, 'update it with git pull'):
                remote.status(TARGET)
        with self.answer(stdout='no json here\n'):
            with self.assertRaises(remote.RemoteError):
                remote.status(TARGET)
        with patch.object(remote.subprocess, 'run', side_effect=subprocess.TimeoutExpired('ssh', 60)):
            with self.assertRaises(remote.RemoteError):
                remote.status(TARGET)


class Link(Fixture):
    def test_link_checks_the_server_before_writing(self):
        inst = self.root.resolve() / 'here' / '.teams'
        with patch.object(remote, 'status', side_effect=remote.RemoteError('sky-a:~/p: unreachable')):
            with self.assertRaises(remote.RemoteError):
                remote.link('sky-a:~/p', str(inst))
        self.assertFalse((inst / 'remote.json').exists())
        st = {'up': True, 'engine': '0.2.0', 'teams': [{'name': 'manager'}, {'name': 'web'}]}
        out = io.StringIO()
        with patch.object(remote, 'status', return_value=st), contextlib.redirect_stdout(out):
            self.assertEqual(remote.link('sky-a:~/p', str(inst)), 0)
        self.assertEqual(json.loads((inst / 'remote.json').read_text()), {'host': 'sky-a', 'path': '~/p'})
        self.assertIn('manager, web', out.getvalue())
        self.assertNotIn('(was ', out.getvalue())
        out = io.StringIO()
        with patch.object(remote, 'status', return_value=st), contextlib.redirect_stdout(out):
            remote.link('other:/srv/p', str(inst))
        self.assertIn('(was sky-a:~/p)', out.getvalue())
        self.assertEqual(json.loads((inst / 'remote.json').read_text()), {'host': 'other', 'path': '/srv/p'})

    def test_strip_option_removes_both_spellings(self):
        self.assertEqual(remote.strip_option(['--remote', 'h:p', 'task', 'list'], '--remote'), ['task', 'list'])
        self.assertEqual(remote.strip_option(['--remote=h:p', 'status'], '--remote'), ['status'])
        self.assertEqual(remote.strip_option(['msg', 'web', '--remote-ish'], '--remote'), ['msg', 'web', '--remote-ish'])
        # only ahead of the command: from the command on, the words are its own and travel untouched
        self.assertEqual(remote.strip_option(['--remote=a:p', '--remote', 'b:p', 'msg', 'web', '--', '--remote', 'next', 'word'], '--remote'),
                         ['msg', 'web', '--', '--remote', 'next', 'word'])
        self.assertEqual(remote.strip_option(['msg', 'web', '--remote=is broken'], '--remote'), ['msg', 'web', '--remote=is broken'])
        self.assertEqual(remote.strip_option(['--remote', 'h:p', '--', 'status'], '--remote'), ['--', 'status'])


class Dispatch(Fixture):
    """bin/teams main(): which commands go remote, with which arguments."""
    def setUp(self):
        super().setUp()
        self.launcher = module('launcher_remote_' + self._testMethodName, 'teams')
        self.project = self.root.resolve() / 'proj'
        (self.project / 'sub').mkdir(parents=True)
        (self.project / '.teams').mkdir()
        (self.project / '.teams' / 'remote.json').write_text(json.dumps({'host': 'sky-a', 'path': '~/p'}))

    def dispatch(self, argv, cwd=None, env=None):
        """main() with argv; the (target, argv) handed to remote.main, or None when the command ran here."""
        launcher, seen = self.launcher, []
        def fake_main(target, a, rest):
            seen.append((target, rest))
            return 0
        environ = {'TEAMS_CONFIG': '', 'TEAMS_REMOTE': '', **(env or {})}
        with patch.object(launcher.sys, 'argv', ['teams', *argv]), patch.dict(os.environ, environ), \
             patch.object(launcher.Path, 'cwd', return_value=cwd or self.project / 'sub'), \
             patch.object(launcher.remote, 'main', side_effect=fake_main), \
             patch.object(launcher, 'load', side_effect=RuntimeError('ran here')), \
             patch.object(launcher, 'cmd_init', side_effect=RuntimeError('ran here')):
            try:
                launcher.main()
            except SystemExit:
                if seen:
                    return seen[0]
                raise
            except RuntimeError:
                return None
        return seen[0] if seen else None

    def test_a_remote_json_above_the_cwd_sends_the_command_there(self):
        target, rest = self.dispatch(['task', 'list'])
        self.assertEqual((target['host'], target['path']), ('sky-a', '~/p'))
        self.assertEqual(rest, ['task', 'list'])

    def test_the_flag_wins_and_is_not_relayed(self):
        target, rest = self.dispatch(['--remote', 'other:/srv/x', 'status'])
        self.assertEqual(target, {'host': 'other', 'path': '/srv/x'})
        self.assertEqual(rest, ['status'])
        _, rest = self.dispatch(['--remote', 'other:/srv/x', 'msg', 'web', '--', '--remote', 'next', 'word'])
        self.assertEqual(rest, ['msg', 'web', '--', '--remote', 'next', 'word'])  # the message keeps its words
        # one spelling only: an abbreviation would reach the server unstripped and be relayed again from there
        for short in (['--r', 'other:/srv/x'], ['--remot', 'other:/srv/x'], ['--rem=other:/srv/x']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                self.dispatch([*short, 'status'])
            self.assertEqual(caught.exception.code, 2, short)

    def test_config_and_teams_config_keep_the_instance_local(self):
        self.assertIsNone(self.dispatch(['--config', str(self.root / 'teams.json'), 'status']))
        self.assertIsNone(self.dispatch(['status'], env={'TEAMS_CONFIG': str(self.root / 'teams.json')}))

    def test_teams_remote_applies_but_init_never_walks(self):
        target, _ = self.dispatch(['status'], cwd=self.root.resolve(), env={'TEAMS_REMOTE': 'env-host:/srv/y'})
        self.assertEqual(target['host'], 'env-host')
        self.assertIsNone(self.dispatch(['init', '--dry-run']))                  # a remote.json above does not capture init
        _, rest = self.dispatch(['--remote', 'h:/p', 'init', '--dry-run'])       # the flag does
        self.assertEqual(rest, ['init', '--dry-run'])

    def test_remote_and_config_together_are_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.dispatch(['--remote', 'h:/p', '--config', str(self.root / 'teams.json'), 'status'])
        self.assertEqual(caught.exception.code, 1)

    def test_link_is_handled_here(self):
        with patch.object(self.launcher.sys, 'argv', ['teams', 'link', 'sky-a:~/p', '--dir', 'x']), \
             patch.object(self.launcher.remote, 'link', return_value=0) as link:
            self.launcher.main()
        link.assert_called_once_with('sky-a:~/p', 'x')

    def test_attach_goes_remote_and_dies_without_a_target(self):
        target, rest = self.dispatch(['attach'])
        self.assertEqual((target['host'], rest), ('sky-a', ['attach']))
        err = io.StringIO()
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(err):
            self.dispatch(['--config', str(self.root / 'teams.json'), 'attach'])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn('teams link <host>:<path>', err.getvalue())


def status(**changes):
    """What `teams status --json` answers for three teams up in tmux on the server."""
    return {'up': True, 'driver': 'tmux', 'started_at': '2026-10-09T12:00:00', 'engine': remote.ENGINE_VERSION,
            'board': 'http://127.0.0.1:43123', 'teams': [
                {'name': 'manager', 'title': 'Manager', 'primary': True, 'purpose': 'coordinates',
                 'handle': {'session': 'teams-p', 'window': '@1'}, 'status': 'idle'},
                {'name': 'web', 'title': 'Web', 'primary': False, 'purpose': 'front end',
                 'handle': {'session': 'teams-p', 'window': '@2'}, 'status': 'working'},
                {'name': 'web-admin', 'title': 'Admin', 'primary': False, 'purpose': '',
                 'handle': {'session': 'teams-p', 'window': '@3'}, 'status': 'idle'}], **changes}


class Views(Fixture):
    """attach(): which terminals are opened, typed into, left alone or closed, and what is recorded."""
    def setUp(self):
        super().setUp()
        here = self.root.resolve() / 'here' / '.teams'
        self.target = {'host': 'sky-a', 'path': '~/p', '_file': here / 'remote.json'}
        self.state = here / '.state' / 'views.json'
        self.driver = FakeDriver()
        self.alive = False                                   # is the recorded tunnel still running?
        self.fake(remote, 'local_driver', side_effect=lambda target, views=None: self.driver)
        self.fake(remote, '_tunnel_alive', side_effect=lambda tunnel: bool(tunnel.get('pid')) and self.alive)
        self.open_tunnel = self.fake(remote, 'open_tunnel', return_value=4242)
        self.killpg = self.fake(remote.os, 'killpg')

    def fake(self, owner, name, **kw):
        patcher = patch.object(owner, name, **kw)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def attach(self, st=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = remote.attach(self.target, st or status())
        return code, out.getvalue(), err.getvalue()

    def recorded(self):
        return json.loads(self.state.read_text())

    def line(self, team, window, mouse=True):
        return remote.view_line(self.target, 'teams-p', window, team, mouse) + '\n'

    def test_views_open_non_primary_first_and_the_primary_is_selected(self):
        code, out, _ = self.attach()
        self.assertEqual(code, 0)
        self.assertEqual([name for name, _ in self.driver.opened], ['web', 'web-admin', 'manager'])
        self.assertEqual(self.driver.sent, [('win:1', self.line('web', '@2')), ('win:2', self.line('web-admin', '@3')),
                                            ('win:3', self.line('manager', '@1'))])
        self.assertEqual(self.driver.selected, ['win:3'])
        self.assertEqual(self.recorded(), {
            'driver': 'fake', 'started_at': '2026-10-09T12:00:00', 'target': 'sky-a:~/p',
            'handles': {'web': {'win': 'win:1'}, 'web-admin': {'win': 'win:2'}, 'manager': {'win': 'win:3'}},
            'tunnel': {'pid': 4242, 'port': 43123}})
        self.open_tunnel.assert_called_once_with(self.target, 43123, self.state.parent / 'tunnel.log')
        self.assertIn('board → http://127.0.0.1:43123', out)

    def test_a_view_carries_the_title_the_purpose_the_target_and_the_mouse_setting(self):
        self.target['mouse'] = False
        with patch.object(self.driver, 'open', wraps=self.driver.open) as opened:
            self.attach()
        self.assertEqual(opened.call_args_list[0].args, ('web', 'Web', Path.cwd(), 'front end (on sky-a:~/p)'))
        self.assertEqual(opened.call_args_list[1].args, ('web-admin', 'Admin', Path.cwd(), '(on sky-a:~/p)'))
        self.assertEqual(self.driver.sent[0], ('win:1', self.line('web', '@2', mouse=False)))

    def test_a_second_attach_opens_nothing_and_reuses_the_tunnel(self):
        self.attach()
        self.alive = True
        _, out, _ = self.attach()
        self.assertEqual((len(self.driver.opened), len(self.driver.sent)), (3, 3))
        self.open_tunnel.assert_called_once()
        self.killpg.assert_not_called()
        self.assertEqual(self.driver.selected, ['win:3', 'win:3'])
        self.assertIn('[web] view already open win:1', out)
        self.assertEqual(self.recorded()['tunnel'], {'pid': 4242, 'port': 43123})

    def test_a_closed_view_is_reopened_and_a_dead_one_is_typed_into_again(self):
        self.attach()
        self.driver.existing.discard('win:1')                                   # web's terminal was closed
        dead = lambda drv, handle, marker: handle['win'] != 'win:2'             # web-admin's terminal is there, its ssh is gone
        with patch.object(remote, 'view_alive', side_effect=dead) as alive:
            _, out, _ = self.attach()
        self.assertEqual(self.driver.opened[3:], [('web', {'win': 'win:4'})])
        self.assertEqual(self.driver.sent[3:], [('win:4', self.line('web', '@2')), ('win:2', self.line('web-admin', '@3'))])
        self.assertEqual(self.recorded()['handles'], {'web': {'win': 'win:4'}, 'web-admin': {'win': 'win:2'}, 'manager': {'win': 'win:3'}})
        self.assertEqual([call.args[2] for call in alive.call_args_list], ['teams-p-web-admin', 'teams-p-manager'])
        self.assertIn('[web-admin] view reconnected win:2', out)

    def test_a_new_run_over_there_closes_the_stale_views_and_tunnel_first(self):
        self.attach()
        self.alive = True
        self.open_tunnel.return_value = 4343
        self.attach(status(started_at='2026-10-10T08:00:00', board='http://127.0.0.1:43999'))
        self.assertEqual(self.driver.closed, ['win:1', 'win:2', 'win:3'])
        self.killpg.assert_called_once_with(4242, signal.SIGTERM)
        self.assertEqual([name for name, _ in self.driver.opened[3:]], ['web', 'web-admin', 'manager'])
        self.assertEqual(self.driver.selected[-1], 'win:6')
        self.assertEqual((self.recorded()['started_at'], self.recorded()['tunnel']), ('2026-10-10T08:00:00', {'pid': 4343, 'port': 43999}))

    def test_attach_refuses_teams_that_are_down_or_not_in_tmux(self):
        with self.assertRaisesRegex(remote.RemoteError, 'teams up'):
            self.attach(status(up=False))
        with self.assertRaisesRegex(remote.RemoteError, '"terminal": "tmux"'):
            self.attach(status(driver='programa'))
        self.assertEqual(self.driver.opened, [])
        self.assertFalse(self.state.exists())

    def test_another_engine_version_over_there_warns_and_goes_on(self):
        _, _, err = self.attach(status(engine='0.0.9'))
        self.assertIn('0.0.9', err)
        self.assertIn(remote.ENGINE_VERSION, err)
        self.assertEqual(len(self.driver.opened), 3)
        self.assertEqual(self.attach()[2], '')                                  # same engine: silent

    def test_manual_prints_the_commands_and_records_no_handle(self):
        self.driver = terminal.Manual({}, self.root)
        _, out, _ = self.attach()
        self.assertIn('# web\n' + self.line('web', '@2'), out)
        self.assertLess(out.index('# web-admin'), out.index('# manager'))
        self.assertEqual((self.recorded()['driver'], self.recorded()['handles']), ('manual', {}))
        self.assertEqual(self.recorded()['tunnel'], {'pid': 4242, 'port': 43123})   # the board is forwarded all the same

    def test_a_team_without_a_window_over_there_is_reported_and_skipped(self):
        st = status()
        st['teams'][1]['handle'] = None
        _, out, _ = self.attach(st)
        self.assertIn('[web] no terminal over there', out)
        self.assertEqual([name for name, _ in self.driver.opened], ['web-admin', 'manager'])
        self.assertNotIn('web', self.recorded()['handles'])

    def test_a_dead_tunnel_is_reopened_and_a_live_one_follows_the_board_to_another_port(self):
        self.attach()
        self.attach()                                                           # the recorded tunnel died: a new one
        self.assertEqual(self.open_tunnel.call_count, 2)
        self.killpg.assert_not_called()
        self.alive = True
        self.open_tunnel.return_value = 4343
        self.attach(status(board='http://127.0.0.1:43999'))                     # the board moved: the old forward is useless
        self.killpg.assert_called_once_with(4242, signal.SIGTERM)
        self.assertEqual(self.open_tunnel.call_args.args[1], 43999)
        self.assertEqual(self.recorded()['tunnel'], {'pid': 4343, 'port': 43999})

    def test_a_busy_local_port_prints_the_forward_to_run_by_hand(self):
        self.open_tunnel.return_value = None
        _, out, _ = self.attach()
        self.assertIn("'ssh' '-N' '-L' '43123:127.0.0.1:43123' 'sky-a'", out)    # quoted, ready to paste in any shell
        self.assertNotIn('board →', out)
        self.assertEqual(self.recorded()['tunnel'], {})

    def test_no_board_over_there_means_no_tunnel(self):
        self.attach()
        self.alive = True
        self.open_tunnel.reset_mock()
        _, out, _ = self.attach(status(board=None))
        self.open_tunnel.assert_not_called()
        self.killpg.assert_called_once_with(4242, signal.SIGTERM)               # the forward of a board that is gone
        self.assertNotIn('board', out)
        self.assertEqual(self.recorded()['tunnel'], {})

    def test_views_opened_before_a_failure_stay_recorded(self):
        typed = self.driver.send
        self.driver.send = lambda handle, text: handle['win'] != 'win:2' and typed(handle, text)
        with self.assertRaisesRegex(remote.RemoteError, 'web-admin'):
            self.attach()
        self.assertEqual(self.recorded()['handles'], {'web': {'win': 'win:1'}, 'web-admin': {'win': 'win:2'}})   # `teams down` can close them


FAKE_SSH = '''n=$(($(cat "$CALLS/count" 2>/dev/null || echo 0) + 1)); echo "$n" > "$CALLS/count"
printf '%s\\n' "$@" > "$CALLS/ssh.$n"
step=$(sed -n "${n}p" "$CALLS/steps")
case "$step" in
  serve) for last; do :; done; exec "$SERVER_SHELL" -c "$last" ;;
  hold) exec sleep 30 ;;
  *) exit "$step" ;;
esac'''


class Lines(Fixture):
    """The lines handed to a shell, run by real shells against a fake ssh, tmux and infocmp: the
    terminal's shell types the view line, the server's shell reads what ssh carries."""
    def setUp(self):
        super().setUp()
        self.bin, self.calls = self.root.resolve() / 'fakebin', self.root.resolve() / 'calls'
        self.bin.mkdir()
        self.calls.mkdir()
        self.script('ssh', FAKE_SSH)                         # follows $CALLS/steps: an exit code, `serve` (run the line) or `hold`
        self.script('tmux', 'printf \'%s\\n\' "$TERM" "$@" > "$CALLS/tmux"; exit 7')
        self.script('infocmp', '[ "$1" != xterm-ghostty ]')  # the server knows every terminal but ghostty's
        self.script('login-shell', '[ "$1" = -lc ] || exit 99; exec "$SERVER_SHELL" -c "$2"')   # "$SHELL" -lc, without start-up files
        home = self.root.resolve() / 'home'                  # no start-up file in it
        home.mkdir()
        self.env = {'PATH': f'{self.bin}:/usr/bin:/bin', 'CALLS': str(self.calls), 'HOME': str(home), 'ZDOTDIR': str(home),
                    'ENV': '', 'SHELL': str(self.bin / 'login-shell'), 'SERVER_SHELL': '/bin/sh'}

    def script(self, name, body):
        (self.bin / name).write_text('#!/bin/sh\n' + body + '\n')
        (self.bin / name).chmod(0o755)

    def ssh_calls(self):
        return [f.read_text().splitlines() for f in sorted(self.calls.glob('ssh.*'))]

    def view(self, steps, term='xterm-ghostty', mouse=True, shell='/bin/sh', **extra):
        """Type a view line into `shell`, whose ssh follows `steps` and hands the server's side to `shell`
        as well: the finished process and what tmux received."""
        for f in self.calls.iterdir():
            f.unlink()
        (self.calls / 'steps').write_text('\n'.join(steps) + '\n')
        with patch.object(remote, 'RETRY', 0):
            line = remote.view_line({'host': 'sky-a', 'path': '~/p', **extra}, 'teams-p', '@3', 'web', mouse)
        r = subprocess.run([shell, '-c', line], capture_output=True, text=True, timeout=20,
                           env={**self.env, 'TERM': term, 'SERVER_SHELL': shell}, cwd=self.env['HOME'])
        tmux = (self.calls / 'tmux').read_text().splitlines() if (self.calls / 'tmux').exists() else None
        return r, tmux

    def wait_for(self, condition, seconds=10):
        deadline = time.monotonic() + seconds
        while not condition():
            if time.monotonic() > deadline:
                self.fail('timed out')
            time.sleep(0.05)

    def test_view_line_exact_strings_with_and_without_mouse(self):
        q = remote.quote
        attach = "'tmux' 'new-session' '-A' '-s' 'teams-p-web' '-t' '=teams-p' ';' 'select-window' '-t' 'teams-p-web:@3'"
        mouse = " ';' 'set-option' '-t' 'teams-p-web' 'mouse' 'on'"
        def line(tmux):
            inner = 'infocmp "$TERM" >/dev/null 2>&1 || export TERM=xterm-256color; exec ' + tmux
            ssh = "'ssh' '-t' '-o' 'ServerAliveInterval=15' '-o' 'ServerAliveCountMax=3' 'sky-a' " + q('exec "$SHELL" -lc ' + q(inner))
            return 'sh -c ' + q(f'while :; do {ssh}; code=$?; [ "$code" -eq 255 ] || exit "$code"; '
                                "echo 'teams-p-web: connection lost, retrying in 3 s'; sleep 3; done")
        target = {'host': 'sky-a', 'path': '~/p'}
        self.assertEqual(remote.view_line(target, 'teams-p', '@3', 'web'), line(attach + mouse))
        self.assertEqual(remote.view_line(target, 'teams-p', '@3', 'web', mouse=False), line(attach))

    def test_a_view_reconnects_on_255_only_and_attaches_the_team_window(self):
        r, tmux = self.view(['255', '255', 'serve'], ssh_options=['-p', '2222'])
        self.assertEqual(r.returncode, 7)                                       # tmux's own exit code ends the loop
        self.assertEqual(r.stdout.count('teams-p-web: connection lost, retrying in 0 s'), 2)
        calls = self.ssh_calls()
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][:-1], ['-t', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-p', '2222', 'sky-a'])
        self.assertEqual(tmux, ['xterm-256color', 'new-session', '-A', '-s', 'teams-p-web', '-t', '=teams-p', ';',
                                'select-window', '-t', 'teams-p-web:@3', ';', 'set-option', '-t', 'teams-p-web', 'mouse', 'on'])

    def test_a_view_ends_on_any_other_exit_and_keeps_a_terminal_type_the_server_knows(self):
        r, tmux = self.view(['0'])                                              # a detach: no retry, back to the shell
        self.assertEqual((r.returncode, r.stdout, len(self.ssh_calls()), tmux), (0, '', 1, None))
        r, tmux = self.view(['serve'], term='vt100', mouse=False)
        self.assertEqual(tmux, ['vt100', 'new-session', '-A', '-s', 'teams-p-web', '-t', '=teams-p', ';',
                                'select-window', '-t', 'teams-p-web:@3'])

    def test_view_alive_looks_for_the_view_session_on_the_terminal_tty(self):
        drv = SimpleNamespace(tty=lambda handle: '/dev/ttys004')
        typed = shlex.split(remote.view_line({'host': 'sky-a', 'path': '~/p'}, 'teams-p', '@3', 'web-admin'))
        ps = '-zsh\n' + ' '.join(typed) + '\n'            # what ps shows of the loop typed into the terminal: its words, unquoted
        with patch.object(remote.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=ps, stderr='')) as run:
            self.assertTrue(remote.view_alive(drv, {}, 'teams-p-web-admin'))
            self.assertFalse(remote.view_alive(drv, {}, 'teams-p-web'))         # the start of another view's name is not this view
            self.assertFalse(remote.view_alive(drv, {}, 'p-web-admin'))         # nor its end
        self.assertEqual(run.call_args.args[0], ['ps', '-ww', '-t', 'ttys004', '-o', 'command='])
        with patch.object(remote.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='-zsh\n', stderr='')):
            self.assertFalse(remote.view_alive(drv, {}, 'teams-p-web'))         # a shell and nothing else: the view is gone

    def test_view_alive_is_true_when_the_terminal_cannot_be_read(self):
        with patch.object(remote.subprocess, 'run') as run:
            self.assertTrue(remote.view_alive(SimpleNamespace(tty=lambda handle: None), {}, 'teams-p-web'))
        run.assert_not_called()
        drv = SimpleNamespace(tty=lambda handle: 'ttys004')
        unknown = SimpleNamespace(returncode=1, stdout='', stderr='ps: /dev/ttys004: No such file or directory\n')
        with patch.object(remote.subprocess, 'run', return_value=unknown):
            self.assertTrue(remote.view_alive(drv, {}, 'teams-p-web'))
        with patch.object(remote.subprocess, 'run', side_effect=OSError('no ps')):
            self.assertTrue(remote.view_alive(drv, {}, 'teams-p-web'))

    def test_port_free_sees_a_listener_on_the_loopback(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen()
            port = listener.getsockname()[1]
            self.assertFalse(remote.port_free(port))
            with patch.object(remote.subprocess, 'Popen') as popen:
                self.assertIsNone(remote.open_tunnel({'host': 'sky-a', 'path': '~/p'}, port, self.root / 'tunnel.log'))
            popen.assert_not_called()                                           # a busy port starts no loop
        self.assertTrue(remote.port_free(port))

    def test_the_tunnel_is_a_background_loop_killed_with_its_whole_group(self):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        (self.calls / 'steps').write_text('255\nhold\n')
        log = self.root.resolve() / 'state' / 'tunnel.log'
        started, popen = [], subprocess.Popen
        def keep(*args, **kw):                               # hold the process object: the test reaps it
            started.append(popen(*args, **kw))
            return started[-1]
        with patch.dict(os.environ, self.env), patch.object(remote, 'RETRY', 0), patch.object(remote.subprocess, 'Popen', side_effect=keep):
            pid = remote.open_tunnel({'host': 'sky-a', 'path': '~/p'}, port, log)
        tunnel = {'pid': pid, 'port': port}
        def gone():
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                return True
            return False
        self.addCleanup(lambda: gone() or os.killpg(pid, signal.SIGKILL))
        self.wait_for(lambda: (self.calls / 'ssh.2').exists())                 # 255 once, then a connection that holds
        self.assertEqual(os.getpgid(pid), pid)                                  # its own process group
        self.assertEqual(self.ssh_calls()[0], ['-N', '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=15', '-o',
                                               'ServerAliveCountMax=3', '-L', f'{port}:127.0.0.1:{port}', 'sky-a'])
        self.assertIn(f'board tunnel {port}: connection lost, retrying in 0 s', log.read_text())
        self.assertTrue(remote._tunnel_alive(tunnel))
        self.assertFalse(remote._tunnel_alive({'pid': pid, 'port': port + 1}))  # this pid, another forward: not that tunnel
        remote.close_tunnel({'tunnel': tunnel})
        started[0].wait(timeout=10)
        self.wait_for(gone)                                                     # the loop, its ssh: nothing is left

    def test_close_tunnel_spares_a_pid_that_is_no_longer_the_tunnel(self):
        views = {'tunnel': {'pid': 4242, 'port': 43123}}
        ps = lambda stdout, code=0: patch.object(remote.subprocess, 'run', return_value=SimpleNamespace(returncode=code, stdout=stdout, stderr=''))
        with patch.object(remote.os, 'killpg') as killpg:
            with ps('/Applications/Mail.app/Contents/MacOS/Mail\n'):            # the pid was taken by another program after a reboot
                remote.close_tunnel(views)
            with ps('', code=1):                                                # nothing runs under it
                remote.close_tunnel(views)
            remote.close_tunnel({})
            killpg.assert_not_called()
            with ps("sh -c while :; do 'ssh' '-N' '-L' '43123:127.0.0.1:43123' 'sky-a'; code=$?; done\n"):
                remote.close_tunnel(views)
        killpg.assert_called_once_with(4242, signal.SIGTERM)

    def under(self, name):
        """The view line typed into `name` and read over there by `name`: tmux gets every word as written."""
        shell = next((p for p in (f'/bin/{name}', f'/usr/bin/{name}', f'/usr/local/bin/{name}', f'/opt/homebrew/bin/{name}') if os.path.exists(p)), None)
        if not shell:
            self.skipTest(f'{name} is not installed here')
        r, tmux = self.view(['serve'], shell=shell)
        self.assertEqual(r.returncode, 7, r.stderr)                             # tmux ran, and its code ended the loop
        self.assertEqual(tmux, ['xterm-256color', 'new-session', '-A', '-s', 'teams-p-web', '-t', '=teams-p', ';',
                                'select-window', '-t', 'teams-p-web:@3', ';', 'set-option', '-t', 'teams-p-web', 'mouse', 'on'])

    def test_a_view_under_sh(self):
        self.under('sh')

    def test_a_view_under_bash(self):
        self.under('bash')

    def test_a_view_under_zsh(self):
        self.under('zsh')

    def test_a_view_under_dash(self):
        self.under('dash')

    def test_a_view_under_ksh(self):
        self.under('ksh')

    def test_state_file_sits_beside_remote_json_or_under_the_user_state_directory(self):
        beside = self.root / 'proj' / '.teams' / 'remote.json'
        self.assertEqual(remote.state_file({'host': 'h', 'path': '/p', '_file': beside}), self.root / 'proj' / '.teams' / '.state' / 'views.json')
        with patch.dict(os.environ, {'HOME': str(self.root)}):
            self.assertEqual(remote.state_file({'host': 'me@Sky-A', 'path': '~/work/My Project'}),
                             self.root / '.local' / 'state' / 'teams' / 'me-sky-a-work-my-project' / 'views.json')

    def test_the_local_driver_is_the_recorded_one_else_the_one_remote_json_asks_for(self):
        target = {'host': 'h', 'path': '/p', 'terminal': 'manual', '_file': self.root / 'proj' / '.teams' / 'remote.json'}
        drv = remote.local_driver(target)
        self.assertEqual((drv.name, drv.root, '_file' in drv.cfg), ('manual', self.root / 'proj' / '.teams', False))
        recorded = remote.local_driver(target, {'driver': 'tmux'})
        self.assertEqual((recorded.name, recorded.session), ('tmux', 'teams-proj'))
        self.assertEqual((remote.board_port('http://127.0.0.1:43123'), remote.board_port(None)), (43123, None))


class Lifecycle(Fixture):
    """up, down and main: what runs over there, then what happens here."""
    def test_up_refuses_teams_already_up_and_points_to_attach(self):
        with patch.object(remote, 'status', return_value={'up': True}), patch.object(remote, 'run') as run:
            with self.assertRaisesRegex(remote.RemoteError, 'teams attach'):
                remote.up(TARGET, False)
        run.assert_not_called()

    def test_up_starts_the_teams_over_there_then_opens_the_views(self):
        before, after = {'up': False}, {'up': True, 'started_at': 'now'}
        with patch.object(remote, 'status', side_effect=[before, after]), patch.object(remote, 'run', return_value=0) as run, \
             patch.object(remote, 'attach', return_value=0) as attach:
            self.assertEqual(remote.up(TARGET, False), 0)
        run.assert_called_once_with(TARGET, ['up'])
        attach.assert_called_once_with(TARGET, after)                           # the status read after the start

    def test_up_resume_goes_through_when_up_and_a_failed_start_opens_nothing(self):
        with patch.object(remote, 'status', return_value={'up': True}), patch.object(remote, 'run', return_value=0) as run, \
             patch.object(remote, 'attach', return_value=0) as attach:
            self.assertEqual(remote.up(TARGET, True), 0)
        run.assert_called_once_with(TARGET, ['up', '--resume'])
        attach.assert_called_once()
        with patch.object(remote, 'status', return_value={'up': False}), patch.object(remote, 'run', return_value=3), \
             patch.object(remote, 'attach') as attach:
            self.assertEqual(remote.up(TARGET, False), 3)
        attach.assert_not_called()

    def test_down_stops_the_server_first_then_closes_views_tunnel_and_state(self):
        target = {'host': 'sky-a', 'path': '~/p', '_file': self.root / 'here' / '.teams' / 'remote.json'}
        state = remote.state_file(target)
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({'driver': 'fake', 'started_at': 'now', 'target': 'sky-a:~/p', 'tunnel': {'pid': 4242, 'port': 43123},
                                     'handles': {'web': {'win': 'win:1'}, 'manager': {'win': 'win:2'}, 'closed': {'win': 'win:9'}}}))
        driver, closed_when_told = FakeDriver(), []
        driver.existing.update({'win:1', 'win:2'})
        def told(target, argv):
            closed_when_told.append((argv, list(driver.closed)))
            return 5
        with patch.object(remote, 'run', side_effect=told), patch.object(remote, 'local_driver', return_value=driver), \
             patch.object(remote, '_tunnel_alive', return_value=True), patch.object(remote.os, 'killpg') as killpg, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(remote.down(target), 5)                            # the remote exit code, whatever was closed here
        self.assertEqual(closed_when_told, [(['down'], [])])                    # the server is told before any view is closed
        self.assertEqual(driver.closed, ['win:1', 'win:2'])                     # a view already gone is left alone
        killpg.assert_called_once_with(4242, signal.SIGTERM)
        self.assertFalse(state.exists())

    def test_main_routes_up_attach_and_down_and_relays_the_rest(self):
        st = {'up': True}
        with patch.object(remote, 'up', return_value=0) as up, patch.object(remote, 'attach', return_value=0) as attach, \
             patch.object(remote, 'down', return_value=4) as down, patch.object(remote, 'status', return_value=st), \
             patch.object(remote, 'relay') as relay:
            self.assertEqual(remote.main(TARGET, SimpleNamespace(cmd='up', dry_run=False, resume=True), ['up', '--resume']), 0)
            up.assert_called_once_with(TARGET, True)
            remote.main(TARGET, SimpleNamespace(cmd='up', dry_run=True, resume=False), ['up', '--dry-run'])
            relay.assert_called_once_with(TARGET, ['up', '--dry-run'])          # a dry run is the server's business
            up.assert_called_once()
            self.assertEqual(remote.main(TARGET, SimpleNamespace(cmd='attach'), ['attach']), 0)
            attach.assert_called_once_with(TARGET, st)
            self.assertEqual(remote.main(TARGET, SimpleNamespace(cmd='down'), ['down']), 4)
            down.assert_called_once_with(TARGET)
