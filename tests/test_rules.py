import unittest
from datetime import date, timedelta

from ocir_checker.model import Image, Repo
from ocir_checker.rules import (
    exit_code,
    rule_empty_repo,
    rule_latest_only,
    rule_public_prod_like,
    rule_stale_latest,
    run_all,
)

AS_OF = date(2026, 11, 20)


def img(tag="v1.0.0", days_old=5):
    return Image(tag=tag, pushed_at=AS_OF - timedelta(days=days_old))


def repo(name="r", public=False, images=(img(),)):
    return Repo(name=name, is_public=public, images=tuple(images))


class TestOcir001(unittest.TestCase):
    def test_fires_public_prod_tag(self):
        out = rule_public_prod_like((repo(public=True, images=[img(tag="prod")]),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_fires_release_and_stable(self):
        out = rule_public_prod_like((repo(public=True, images=[img(tag="release"), img(tag="stable")]),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertIn("release", out[0].detail)

    def test_quiet_private_repo(self):
        self.assertEqual(rule_public_prod_like((repo(public=False, images=[img(tag="prod")]),), AS_OF), [])

    def test_quiet_public_without_prod_tags(self):
        self.assertEqual(rule_public_prod_like((repo(public=True, images=[img(tag="v1.0.0")]),), AS_OF), [])


class TestOcir002(unittest.TestCase):
    def test_fires_latest_only(self):
        out = rule_latest_only((repo(images=[img(tag="latest"), img(tag="latest")]),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_quiet_with_version_tag(self):
        self.assertEqual(rule_latest_only((repo(images=[img(tag="latest"), img(tag="v1.0.0")]),), AS_OF), [])

    def test_empty_repo_not_flagged_here(self):
        self.assertEqual(rule_latest_only((repo(images=()),), AS_OF), [])


class TestOcir003(unittest.TestCase):
    def test_fires_empty(self):
        out = rule_empty_repo((repo(images=()),), AS_OF)
        self.assertEqual(len(out), 1)

    def test_quiet_nonempty(self):
        self.assertEqual(rule_empty_repo((repo(),), AS_OF), [])


class TestOcir004(unittest.TestCase):
    def test_fires_stale_latest(self):
        out = rule_stale_latest((repo(images=[img(tag="latest", days_old=200)]),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "LOW")

    def test_boundary_180_quiet(self):
        self.assertEqual(rule_stale_latest((repo(images=[img(tag="latest", days_old=180)]),), AS_OF), [])

    def test_version_tags_ignored(self):
        self.assertEqual(rule_stale_latest((repo(images=[img(tag="v1.0.0", days_old=400)]),), AS_OF), [])


class TestAggregation(unittest.TestCase):
    def test_exit_2_on_high(self):
        self.assertEqual(exit_code(run_all((repo(public=True, images=[img(tag="prod")]),), AS_OF)), 2)

    def test_exit_1_medium_only(self):
        self.assertEqual(exit_code(run_all((repo(images=[img(tag="latest")]),), AS_OF)), 1)

    def test_exit_0_clean(self):
        self.assertEqual(exit_code(run_all((repo(),), AS_OF)), 0)


if __name__ == "__main__":
    unittest.main()
