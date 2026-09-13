from concurrent.futures import ThreadPoolExecutor
from support import Fixture
import tasklib

class Tickets(Fixture):
    def test_content_edits_are_quiet_and_operational_changes_are_logged(self):
        tid = self.task()['id']
        before = tasklib.load(self.shared, tid)['log']
        tasklib.update(self.shared, tid, {'title': 'Clearer title', 'criteria': 'Updated criteria'})
        self.assertEqual(tasklib.load(self.shared, tid)['log'], before)
        tasklib.update(self.shared, tid, {'status': 'doing', 'blocked': True})
        changed = tasklib.load(self.shared, tid)['log']
        self.assertEqual(len(changed), len(before) + 1)
        self.assertIn('status todo → doing', changed[-1])
        self.assertIn('blocked False → True', changed[-1])
        tasklib.update(self.shared, tid, {'status': 'doing', 'blocked': True})
        self.assertEqual(tasklib.load(self.shared, tid)['log'], changed)

    def test_concurrent_notes_are_not_lost(self):
        tid = self.task()['id']
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda n: tasklib.append_log(self.shared, tid, f'unique-note-{n}'), range(40)))
        log = tasklib.load(self.shared, tid)['log']
        for n in range(40):
            self.assertEqual(sum(line.endswith(f'unique-note-{n}') for line in log), 1)

    def test_concurrent_ids(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(lambda _: self.task()['id'], range(24)))
        self.assertEqual(len(set(ids)), 24)

    def test_header_body_reference_does_not_change_other_ticket(self):
        one, two = self.doing(), self.doing()
        tasklib.apply_message(self.shared, 'backend', 'gestion', f'DONE {one} | follow up in {two}')
        self.assertEqual(tasklib.load(self.shared, one)['status'], 'qa')
        self.assertEqual(tasklib.load(self.shared, two)['status'], 'doing')

    def test_only_manager_dispatches_and_backlog_stays_human_owned(self):
        tid = self.task()['id']
        with self.assertRaises(ValueError):
            tasklib.apply_message(self.shared, 'backend', 'backend', f'TASK {tid} | self assign')
        tasklib.update(self.shared, tid, {'status': 'backlog'})
        with self.assertRaises(ValueError):
            tasklib.apply_message(self.shared, 'gestion', 'backend', f'TASK {tid} | take backlog')

    def test_wrong_owner_cannot_complete(self):
        tid = self.doing()
        with self.assertRaises(ValueError):
            tasklib.apply_message(self.shared, 'frontend', 'gestion', f'DONE {tid} | complete')

    def test_replay_is_idempotent_even_after_other_messages(self):
        tid = self.doing()
        tasklib.apply_message(self.shared, 'backend', 'gestion', f'DONE {tid} | ready', event_id='done')
        tasklib.append_log(self.shared, tid, 'a later note')
        before = tasklib.path_of(self.shared, tid).read_text()
        tasklib.apply_message(self.shared, 'backend', 'gestion', f'DONE {tid} | ready', event_id='done')
        self.assertEqual(before, tasklib.path_of(self.shared, tid).read_text())

    def test_batch_validates_before_writing(self):
        one = self.doing()
        two = self.task()['id']
        with self.assertRaises(ValueError):
            tasklib.apply_message(self.shared, 'backend', 'gestion', f'DONE {one},{two} | ready')
        self.assertEqual(tasklib.load(self.shared, one)['status'], 'doing')

    def test_primary_closes_after_qa_and_preserves_history(self):
        tid = self.doing()
        with self.assertRaises(ValueError):
            tasklib.update(self.shared, tid, {'status': 'done'}, actor='gestion')
        tasklib.apply_message(self.shared, 'backend', 'gestion', f'DONE {tid} | ready')
        tasklib.append_log(self.shared, tid, 'gestion: test passed', actor='gestion')
        tasklib.update(self.shared, tid, {'status': 'done'}, actor='gestion')
        self.assertTrue(any('test passed' in line for line in tasklib.load(self.shared, tid)['log']))
        tasklib.delete(self.shared, tid)
        self.assertFalse(tasklib.path_of(self.shared, tid).exists())


    def test_primary_can_edit_while_owner_cannot_self_approve(self):
        tid = self.doing()
        tasklib.update(self.shared, tid, {'scope': 'other.py'}, actor='gestion')
        self.assertEqual(tasklib.load(self.shared, tid)['scope'], 'other.py')
        with self.assertRaises(ValueError):
            tasklib.update(self.shared, tid, {'title': 'new'}, actor='backend')
