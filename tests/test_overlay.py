import sys
import tempfile
import unittest
import json
import subprocess
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from sc.adapt import adapt
from sc.discover import source_fingerprint, overlay_fingerprint
from sc.install_into_fork import install
from sc import release


class OverlayTests(unittest.TestCase):
    def test_deterministic_fingerprint(self):
        a = {"merge": "abc", "sarasa": "v1"}
        self.assertEqual(source_fingerprint(a), source_fingerprint(dict(reversed(list(a.items())))))
        self.assertNotEqual(source_fingerprint(a), source_fingerprint({"merge": "def", "sarasa": "v1"}))

    def test_adaptation_and_fail_closed_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "src").mkdir()
            (root / "config.yaml").write_text('family_name: "SarasaMonoTCEmoji"\nbase_font: "SarasaMonoTC-Regular.ttf"\nurl: "https://github.com/sspig0127/SarasaMonoTC-Emoji"\n', encoding='utf-8')
            (root / "build.py").write_text('"SarasaMonoTCEmoji"', encoding='utf-8')
            (root / "tests" / "conftest.py").write_text('"SarasaMonoTC-Regular.ttf"', encoding='utf-8')
            changed = adapt(root, 'someone/SarasaMonoSC-Emoji')
            self.assertIn('config.yaml', changed)
            self.assertIn('tests/conftest.py', changed)
            result = (root / 'config.yaml').read_text(encoding='utf-8')
            self.assertIn('SarasaMonoSC-Regular.ttf', result)
            self.assertIn('https://github.com/someone/SarasaMonoSC-Emoji', result)

    def test_overlay_hash_ignores_keepalive(self):
        root = Path(__file__).resolve().parents[1]
        first = overlay_fingerprint(root)
        keepalive = root / '.github/sc-keepalive.txt'
        try:
            keepalive.write_text('check', encoding='utf-8')
            self.assertEqual(first, overlay_fingerprint(root))
        finally:
            keepalive.unlink(missing_ok=True)

    def test_install_preserves_original_license(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            fork = Path(tmp)
            (fork / '.git').mkdir()
            (fork / 'build.py').write_text('upstream', encoding='utf-8')
            (fork / 'config.yaml').write_text('upstream', encoding='utf-8')
            (fork / 'LICENSE').write_text('original OFL', encoding='utf-8')
            (fork / 'README.md').write_text('original README', encoding='utf-8')
            files = install(root, fork)
            self.assertIn('sc/adapt.py', files)
            self.assertEqual((fork / 'LICENSE').read_text(), 'original OFL')
            self.assertEqual((fork / 'README.md').read_text(), 'original README')
            self.assertTrue((fork / '.github/workflows/sc-autobuild.yml').is_file())

    def test_reject_unknown_upstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                adapt(Path(tmp))


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tag = 'sc-auto-test'
        self.assets = [{'name': name, 'state': 'uploaded', 'size': 3}
                       for name in sorted(release.expected_names(self.tag))]

    def test_skip_only_complete_published_release(self):
        for draft, assets, expected in [(False, self.assets, False), (True, self.assets, True),
                                         (False, self.assets[:-1], True)]:
            with self.subTest(draft=draft, asset_count=len(assets)):
                response = subprocess.CompletedProcess([], 0, json.dumps({'isDraft': draft, 'assets': assets}), '')
                with patch.object(release, 'gh', return_value=response):
                    self.assertEqual(release.should_build('owner/repo', self.tag), expected)
        broken = [dict(asset) for asset in self.assets]
        broken[0]['state'] = 'starter'
        self.assertFalse(release.complete({'assets': broken}, self.tag))

    def test_inspection_errors_do_not_mean_missing_release(self):
        for error in ['HTTP 401: Bad credentials', 'connection reset']:
            with patch.object(release, 'gh', return_value=subprocess.CompletedProcess([], 1, '', error)):
                with self.assertRaises(RuntimeError):
                    release.should_build('owner/repo', self.tag)
        with patch.object(release, 'gh', return_value=subprocess.CompletedProcess([], 1, '', 'release not found')):
            self.assertTrue(release.should_build('owner/repo', self.tag))

    def test_interrupted_upload_resumes_draft_before_publication(self):
        state = {'release': None, 'fail_upload': True}
        calls = []
        def fake_gh(*args):
            calls.append(args)
            operation = args[1]
            if operation == 'view':
                if state['release'] is None:
                    return subprocess.CompletedProcess([], 1, '', 'release not found')
                return subprocess.CompletedProcess([], 0, json.dumps(state['release']), '')
            if operation == 'create':
                self.assertIn('--draft', args)
                state['release'] = {'isDraft': True, 'assets': []}
            elif operation == 'upload':
                self.assertIn('--clobber', args)
                state['release']['assets'] = self.assets[:1]
                if state['fail_upload']:
                    return subprocess.CompletedProcess([], 1, '', 'interrupted upload')
                state['release']['assets'] = self.assets
            elif operation == 'edit':
                self.assertTrue(release.complete(state['release'], self.tag))
                self.assertIn('--draft=false', args)
                state['release']['isDraft'] = False
            return subprocess.CompletedProcess([], 0, '', '')
        with tempfile.TemporaryDirectory() as tmp, patch.object(release, 'gh', side_effect=fake_gh):
            directory = Path(tmp)
            for asset in self.assets:
                (directory / asset['name']).write_bytes(b'zip')
            with self.assertRaisesRegex(RuntimeError, 'interrupted upload'):
                release.publish('owner/repo', self.tag, 'v1', 'sha', directory)
            self.assertTrue(state['release']['isDraft'])
            self.assertFalse(any(call[1] == 'edit' for call in calls))
            self.assertTrue(release.should_build('owner/repo', self.tag))
            state['fail_upload'] = False
            release.publish('owner/repo', self.tag, 'v1', 'sha', directory)
            self.assertFalse(release.should_build('owner/repo', self.tag))
            self.assertEqual(sum(call[1] == 'create' for call in calls), 1)

    def test_size_mismatch_blocks_publication(self):
        current = {'isDraft': True, 'assets': self.assets}
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for asset in self.assets:
                (directory / asset['name']).write_bytes(b'longer')
            with patch.object(release, 'inspect', return_value=current), patch.object(release, 'require') as run:
                with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                    release.publish('owner/repo', self.tag, 'v1', 'sha', directory)
                self.assertFalse(any(call.args[1] == 'edit' for call in run.call_args_list))


class InstallerWorkflowTests(unittest.TestCase):
    def test_archive_tc_workflows_and_keep_install_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            fork = Path(tmp)
            (fork / '.git').mkdir()
            (fork / 'build.py').write_text('upstream')
            (fork / 'config.yaml').write_text('upstream')
            workflows = fork / '.github/workflows'
            workflows.mkdir(parents=True)
            originals = {'release.yml': 'manual TC release', 'check-upstream.yml': 'monthly TC check'}
            for name, contents in originals.items():
                (workflows / name).write_text(contents)
            (workflows / 'test.yml').write_text('upstream CI')
            root = Path(__file__).resolve().parents[1]
            install(root, fork)
            install(root, fork)
            for name, contents in originals.items():
                self.assertFalse((workflows / name).exists())
                self.assertEqual((fork / '.github/upstream-workflows' / name).read_text(), contents)
            self.assertEqual((workflows / 'test.yml').read_text(), 'upstream CI')
            self.assertTrue((workflows / 'sc-autobuild.yml').exists())


if __name__ == '__main__':
    unittest.main()
