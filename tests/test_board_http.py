"""Real loopback HTTP checks, entirely temporary; no terminal or model calls."""
from http.server import ThreadingHTTPServer
import json
import threading
import urllib.error
import urllib.request

from support import Fixture, module
import tasklib


class BoardHTTP(Fixture):
    def test_original_board_flow_with_shared_writer(self):
        board = module('board_http', 'teams-board')
        board.load_ctx(self.root)
        class Server(ThreadingHTTPServer):
            daemon_threads = True
        server = Server(('127.0.0.1', 0), board.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_address[1]}'
        def request(method, path, data=None):
            body = json.dumps(data).encode() if data is not None else None
            req = urllib.request.Request(base + path, data=body, method=method,
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=3) as response:
                return json.load(response)
        with urllib.request.urlopen(base, timeout=3) as page:
            html = page.read().decode()
        self.assertIn('openTicket', html)
        for field in ('scope','verify','decisions','depends'):
            self.assertIn('id="t-' + field + '"', html)
        created = request('POST', '/api/tasks', {'title': 'HTTP audit'})
        tid = created['id']
        ticket = request('PATCH', '/api/tasks/' + tid, {'status': 'todo', 'team': 'backend',
            'scope': 'app.py', 'verify': 'python3 -m unittest', 'criteria': 'test passes'})
        self.assertEqual(ticket['scope'], 'app.py')
        tasklib.apply_message(self.shared, 'manager', 'backend', f'TASK {tid} | implement')
        request('PATCH', '/api/tasks/' + tid, {'scope': 'another.py'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            request('PATCH', '/api/tasks/' + tid, {'status': 'done'})
        error.exception.close()
        tasklib.apply_message(self.shared, 'backend', 'manager', f'DONE {tid} | verified')
        request('POST', '/api/tasks/' + tid + '/comment', {'text': 'Human inspected result'})
        accepted = request('PATCH', '/api/tasks/' + tid, {'status': 'done'})
        self.assertEqual(accepted['status'], 'done')
        note = request('POST', '/api/tasks/' + tid + '/comment', {'text': 'Kept in history', 'notify': False})
        self.assertTrue(any('Kept in history' in line for line in note['log']))
        loaded = request('GET', '/api/tasks/' + tid)
        self.assertTrue(any('Human inspected result' in line for line in loaded['log']))
        state = request('GET', '/api/state')
        self.assertEqual(state['transitions']['doing'], ['todo', 'qa'])
        self.assertEqual(state['transitions']['qa'], ['doing', 'done'])
        self.assertEqual(state['pending_notifications'], 1)
        self.assertFalse(state['notify_available'])
        request('DELETE', '/api/tasks/' + tid)
        self.assertFalse(tasklib.path_of(self.shared, tid).exists())
