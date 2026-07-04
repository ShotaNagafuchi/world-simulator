import unittest
from pathlib import Path

from frontmatter import parse_frontmatter, coerce
from score import brier, grade

ROOT = Path(__file__).parent.parent


class TestCoerce(unittest.TestCase):
    def test_scalars(self):
        self.assertEqual(coerce("0.7"), 0.7)
        self.assertEqual(coerce("42"), 42)
        self.assertIs(coerce("true"), True)
        self.assertIs(coerce("false"), False)
        self.assertIsNone(coerce("null"))
        self.assertEqual(coerce('"quoted"'), "quoted")
        self.assertEqual(coerce("2028-12-31"), "2028-12-31")

    def test_inline_list(self):
        self.assertEqual(coerce("[LAW-001, LAW-002]"), ["LAW-001", "LAW-002"])
        self.assertEqual(coerce("[]"), [])


class TestParseFrontmatter(unittest.TestCase):
    def test_full_document(self):
        text = (
            "---\n"
            "id: PRED-2026-999\n"
            "probability: 0.7\n"
            "laws: [LAW-003, LAW-004]\n"
            "kill_conditions:\n"
            "  - 条件その1\n"
            "  - 条件その2\n"
            "outcome: null\n"
            "---\n"
            "# 本文\n"
        )
        fm = parse_frontmatter(text)
        self.assertEqual(fm["id"], "PRED-2026-999")
        self.assertEqual(fm["probability"], 0.7)
        self.assertEqual(fm["laws"], ["LAW-003", "LAW-004"])
        self.assertEqual(fm["kill_conditions"], ["条件その1", "条件その2"])
        self.assertIsNone(fm["outcome"])

    def test_no_frontmatter(self):
        self.assertIsNone(parse_frontmatter("# ただのMarkdown\n"))


class TestBrier(unittest.TestCase):
    def test_perfect_and_worst(self):
        self.assertAlmostEqual(brier(0.99, True), 0.0001)
        self.assertAlmostEqual(brier(0.99, False), 0.9801)

    def test_coin_flip(self):
        self.assertAlmostEqual(brier(0.5, True), 0.25)
        self.assertAlmostEqual(brier(0.5, False), 0.25)

    def test_grade_thresholds(self):
        self.assertEqual(grade(0.05), "strong")
        self.assertEqual(grade(0.2), "ok")
        self.assertEqual(grade(0.3), "falsification-pressure")


class TestRepoIntegrity(unittest.TestCase):
    """リポジトリ自体が掟に従っているかの統合テスト。"""

    def test_validate_passes(self):
        import validate
        self.assertEqual(validate.main(), 0)

    def test_all_laws_have_kill_conditions(self):
        from frontmatter import collect
        for path, fm, err in collect(ROOT / "laws"):
            self.assertIsNone(err, f"{path}: {err}")
            self.assertTrue(fm.get("kill_conditions"),
                            f"{path.name}: 殺せない法則は法則ではない")


if __name__ == "__main__":
    unittest.main()
