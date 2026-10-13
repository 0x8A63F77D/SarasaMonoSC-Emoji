import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from sc.adapt import adapt
from sc.discover import source_fingerprint, overlay_fingerprint
from sc.install_into_fork import install


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


if __name__ == '__main__':
    unittest.main()
