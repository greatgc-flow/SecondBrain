"""Only tests the kit utility. These are not product TDD tests."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KitTests(unittest.TestCase):
    def command(self, root, *args):
        return subprocess.run([sys.executable, str(root / 'kit.py'), *args], capture_output=True, text=True, timeout=15)

    def test_help_and_no_command(self):
        self.assertEqual(self.command(ROOT, 'help').returncode, 0)
        self.assertIn('feedback', self.command(ROOT, 'help').stdout)
        self.assertEqual(self.command(ROOT, 'help', 'feedback').returncode, 0)
        self.assertEqual(self.command(ROOT, 'unknown').returncode, 2)

    def test_catalog_summary_complete(self):
        p = self.command(ROOT, 'catalog', '--summary')
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertEqual(data['profiles'], {'generic': 100, 'secondbrain': 188})
        self.assertEqual(data['product_tests'], 'NOT_RUN')

    def test_feedback_append_only_and_independent_close(self):
        with tempfile.TemporaryDirectory(prefix='kit path 한글 ') as td:
            path = Path(td); shutil.copy2(ROOT / 'kit.py', path / 'kit.py')
            created = self.command(path, 'feedback', 'add', '--kind', 'bug', '--title', '경로 공백', '--note', '재현', '--creator','author')
            self.assertEqual(created.returncode, 0, created.stderr)
            id_ = created.stdout.split()[1]
            self.assertTrue(id_.startswith('FB-'))
            denied = self.command(path, 'feedback', 'approve-close', id_, '--reviewer','reviewer','--evidence','x')
            self.assertEqual(denied.returncode, 3)
            propose = self.command(path, 'feedback', 'propose-close', id_, '--release','RC-1','--regression','TC-1',
                                   '--observation','7 days after','--lesson','add edge case','--evidence','report sha256')
            self.assertEqual(propose.returncode, 0, propose.stderr)
            self.assertEqual(self.command(path, 'feedback', 'approve-close', id_, '--reviewer','author','--evidence','x').returncode, 5)
            approval = self.command(path, 'feedback', 'approve-close', id_, '--reviewer','reviewer','--evidence','review note')
            self.assertEqual(approval.returncode, 0, approval.stderr)
            self.assertIn('CLOSED', self.command(path, 'feedback', 'list').stdout)
            self.assertEqual(self.command(path, 'feedback','reopen',id_,'--reason','recurrence').returncode, 0)
            events=(path/'.kit_state/feedback.jsonl').read_text(encoding='utf-8').splitlines()
            self.assertEqual([json.loads(e)['event'] for e in events], ['CREATED','CLOSE_PROPOSED','CLOSE_APPROVED','REOPENED'])

    def test_feedback_corruption_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td); shutil.copy2(ROOT / 'kit.py', path / 'kit.py')
            (path/'.kit_state').mkdir(); (path/'.kit_state/feedback.jsonl').write_text('{bad\n')
            p=self.command(path,'feedback','list')
            self.assertEqual(p.returncode,3)
            self.assertIn('Corrupted',p.stderr)

    def test_relocated_full_tree_and_manifest_tamper(self):
        with tempfile.TemporaryDirectory(prefix='moved root 한글 ') as td:
            target = Path(td) / 'renamed root'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('__pycache__', '.kit_state', '*.pyc'))
            ok = self.command(target, 'verify', '--json')
            self.assertEqual(ok.returncode, 0, ok.stdout[-1200:] + ok.stderr)
            self.assertTrue(json.loads(ok.stdout)['warnings'])
            (target / 'README.md').write_text('unauthorized edit\n', encoding='utf-8')
            denied = self.command(target, 'verify', '--json')
            self.assertEqual(denied.returncode, 3)
            self.assertIn('manifest mismatch: README.md', denied.stdout)

    def test_verify_product_not_run(self):
        p = self.command(ROOT, 'verify', '--json')
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout[-800:])
        data=json.loads(p.stdout)
        self.assertEqual(data['status'],'PASS')
        self.assertIn('product TDD',data['not_run'])

    def test_catalog_search_and_invalid_limit(self):
        self.assertEqual(self.command(ROOT, 'catalog', '--id', 'GD-001', '--json').returncode, 0)
        rows = json.loads(self.command(ROOT, 'catalog', '--id', 'GD-001', '--json').stdout)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['test_id'], 'TEST-001')
        self.assertEqual(self.command(ROOT, 'catalog', '--find', 'should-never-match').returncode, 3)
        self.assertEqual(self.command(ROOT, 'catalog', '--limit', '0').returncode, 3)

    def test_feedback_history_and_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td); shutil.copy2(ROOT/'kit.py', path/'kit.py')
            made = self.command(path, 'feedback', 'add', '--kind', 'task', '--title', '실행 이력', '--note', '착수')
            self.assertEqual(made.returncode, 0, made.stderr)
            uid = made.stdout.split()[1]
            note = self.command(path, 'feedback', 'note', uid, '--kind', 'progress', '--note', '재현완료', '--ref', 'TEST-1')
            self.assertEqual(note.returncode, 0, note.stderr)
            self.assertEqual(self.command(path, 'feedback', 'note', uid, '--kind', 'lesson', '--note', '회귀 강화').returncode, 0)
            v = json.loads(self.command(path, 'feedback', 'verify').stdout)
            self.assertEqual(v['status'], 'PASS')
            self.assertEqual(v['events'], 3)
            shown = json.loads(self.command(path, 'feedback', 'show', uid).stdout)
            self.assertEqual(len(shown['events']), 3)
            self.assertEqual(shown['status'], 'OPEN')
            items=json.loads(self.command(path,'feedback','list','--json').stdout)
            self.assertEqual(items[0]['status'],'OPEN')
            events = [json.loads(z) for z in (path/'.kit_state/feedback.jsonl').read_text().splitlines()]
            self.assertEqual(events[1]['prev_hash'],events[0]['event_hash'])

    def test_feedback_tamper_and_stale_lock_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td); shutil.copy2(ROOT/'kit.py',path/'kit.py')
            a=self.command(path,'feedback','add','--kind','bug','--title','x','--note','y')
            self.assertEqual(a.returncode,0,a.stderr)
            journal=path/'.kit_state/feedback.jsonl'
            orig=journal.read_text(encoding='utf-8')
            journal.write_text(orig.replace('"title":"x"','"title":"y"'),encoding='utf-8')
            self.assertEqual(self.command(path,'feedback','verify').returncode,3)
            self.assertEqual(self.command(path,'feedback','add','--kind','bug','--title','other','--note','x').returncode,3)
            journal.write_text(orig,encoding='utf-8')
            (path/'.kit_state/feedback.lock').write_text('stale',encoding='utf-8')
            blocked=self.command(path,'feedback','add','--kind','bug','--title','other','--note','x')
            self.assertEqual(blocked.returncode,3)
            self.assertIn('locked',blocked.stderr)

    def test_feedback_invalid_close_or_postclose_note(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td); shutil.copy2(ROOT/'kit.py',path/'kit.py')
            made=self.command(path,'feedback','add','--kind','error','--title','x','--note','y','--creator','first')
            uid=made.stdout.split()[1]
            self.assertEqual(self.command(path,'feedback','propose-close',uid,'--release','r', '--regression','t', '--observation','o', '--lesson','l', '--evidence','e').returncode,0)
            self.assertEqual(self.command(path,'feedback','approve-close',uid,'--reviewer','second','--evidence','signed').returncode,0)
            self.assertEqual(self.command(path,'feedback','note',uid,'--kind','progress','--note','bad').returncode,3)
            self.assertEqual(self.command(path,'feedback','verify').returncode,0)

    def test_verify_scenarios_static_report(self):
        p=self.command(ROOT,'verify','--json')
        self.assertEqual(p.returncode,0,p.stdout[-600:]+p.stderr)
        data=json.loads(p.stdout)
        self.assertGreater(data['checks']['scenarios'],0)
        self.assertEqual(data['checks']['product_status'],'PRE_TDD')

if __name__=='__main__': unittest.main()
