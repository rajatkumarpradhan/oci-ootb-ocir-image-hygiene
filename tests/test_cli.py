import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from ocir_checker.cli import main

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


class TestCli(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_messy_sample_exits_2_and_covers_rules(self):
        code, out, _ = self.run_cli([os.path.join(SAMPLES, "ocir_messy.json"), "--as-of", "2026-11-20"])
        self.assertEqual(code, 2)
        for rule in ("OCIR001", "OCIR002", "OCIR003", "OCIR004"):
            self.assertIn(rule, out)

    def test_clean_sample_exits_0(self):
        code, out, _ = self.run_cli([os.path.join(SAMPLES, "ocir_clean.json"), "--as-of", "2026-11-20"])
        self.assertEqual(code, 0)
        self.assertIn("RESULT: clean", out)

    def test_bad_date_exits_2(self):
        doc = '{"repos": [{"name": "r", "images": [{"tag": "t", "pushed_at": "20-11-2026"}]}]}'
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(doc)
            path = fh.name
        try:
            code, _, err = self.run_cli([path])
            self.assertEqual(code, 2)
            self.assertIn("invalid date", err)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
