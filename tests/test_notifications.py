from support import Fixture, module
from unittest.mock import patch
import os
import storage
from concurrent.futures import ThreadPoolExecutor

class Board(Fixture):
    def test_queue_preserves_tail_when_a_later_delivery_fails(self):
        board = module('board_partial', 'teams-board')
        board.load_ctx(self.root)
        for index in range(3):
            board.notify_primary(f'NEW T{index + 1} | ticket')
        with patch.object(board, '_send_primary', side_effect=[True, False]):
            board.retry_pending()
        pending = storage.read_json(self.root / '.state/notifications.json')
        self.assertEqual([p['text'] for p in pending], ['NEW T2 | ticket', 'NEW T3 | ticket'])

    def test_enqueue_during_delivery_preserves_new_item(self):
        board = module('board_new_item', 'teams-board')
        board.load_ctx(self.root)
        board.notify_primary('NEW T1 | first')
        def send(text):
            if text == 'NEW T1 | first':
                # A different request thread must be able to append while terminal I/O waits.
                with ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(board.notify_primary, 'NEW T2 | second').result(timeout=2)
                return True
            return False
        with patch.object(board, '_send_primary', side_effect=send):
            board.retry_pending()
        pending = storage.read_json(self.root / '.state/notifications.json')
        self.assertEqual([p['text'] for p in pending], ['NEW T2 | second'])

    def test_queue_and_channel_changes_update_the_live_state_signature(self):
        board = module('board_signature', 'teams-board')
        board.load_ctx(self.root)
        before = board.state_signature()
        board.notify_primary('NEW T1 | first')
        self.assertNotEqual(before, board.state_signature())
        queued = board.state_signature()
        storage.write_json(self.root / '.state/terminal.json',
                           {'driver': 'programa', 'handles': {'manager': {'workspace': 'workspace:1', 'surface': 'surface:1'}}})
        self.assertNotEqual(queued, board.state_signature())
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': 'surface:9', 'PROGRAMA_SOCKET_PATH': '/tmp/x'}):
            self.assertTrue(board.api_state()['notify_available'])
        with patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': '', 'PROGRAMA_SOCKET_PATH': ''}):
            self.assertFalse(board.api_state()['notify_available'])  # recorded terminal, but no way to reach it from here
        self.assertEqual(board.api_state()['pending_notifications'], 1)

    def test_notifications_survive_restart_and_retry_keeps_tail(self):
        board = module('board_test', 'teams-board')
        board.load_ctx(self.root)
        board.notify_primary('NEW T1 | one')
        board.notify_primary('NEW T2 | two')
        board.notify_primary('NEW T1 | one')
        restarted = module('board_restarted', 'teams-board')
        restarted.load_ctx(self.root)
        with patch.object(restarted, '_send_primary', return_value=False):
            restarted.retry_pending()
        path = self.root / '.state/notifications.json'
        self.assertEqual(len(storage.read_json(path)), 2)
        with patch.object(restarted, '_send_primary', return_value=True):
            restarted.retry_pending()
        self.assertEqual(storage.read_json(path), [])

    def test_unreachable_terminal_preserves_notification_without_programa_call(self):
        board = module('board_no_surface', 'teams-board')
        board.load_ctx(self.root)
        board.notify_primary('NEW T1 | one')
        storage.write_json(self.root / '.state/terminal.json',
                           {'driver': 'programa', 'handles': {'manager': {'workspace': 'workspace:1', 'surface': 'surface:1'}}})
        with patch.object(board.terminal.subprocess, 'run') as run, \
             patch.dict(os.environ, {'PROGRAMA_SURFACE_ID': '', 'PROGRAMA_SOCKET_PATH': ''}):
            board.retry_pending()
            run.assert_not_called()
            self.assertFalse(board.api_state()['notify_available'])
        self.assertEqual(board.api_state()['pending_notifications'], 1)
