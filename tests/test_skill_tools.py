"""Behavioral checks for the portable skill's optional local helpers."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/medical-education-studio"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


init = load("init_project", SKILL / "scripts/init_project.py")
validator = load("validate_project", SKILL / "scripts/validate_project.py")
packager = load("package_skill", ROOT / "tools/package_skill.py")


class SkillToolsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "中文项目"
        init.initialize(self.root, "测试方向", "测试读者", 2)
        self.project = json.loads((self.root / "project.json").read_text(encoding="utf-8"))

    def issues(self, project=None):
        return validator.validate(self.project if project is None else project, self.root)

    def ready(self):
        # Synthetic local fixtures test structural relationships, not medical evidence.
        (self.root / "material.md").write_text("Test-only source material.", encoding="utf-8")
        self.project["topics"]["selected"] = {"topic_id": "t1", "title": "测试选题", "angle": "测试角度"}
        self.project["research"].update(status="ready", sources=[{
            "source_id": "s1", "title": "Test fixture", "locator": "material.md", "accessed_on": "2026-10-21"
        }], claims=[{"claim_id": "c1", "statement": "Test-only claim", "source_ids": ["s1"], "scope": "Synthetic test"}])
        self.project["script"].update(status="ready", title="测试标题", body="测试正文", pages=[
            {"page_id": f"p{i}", "title": "标题", "text": "文字", "visual_brief": "画面", "claim_ids": ["c1"]}
            for i in range(1, 3)
        ])

    def test_initialize_unicode_project_without_confirming_or_running(self):
        self.assertFalse(self.issues())
        self.assertEqual(self.project["intent_info"]["data"]["page_count"], 2)
        self.assertFalse(self.project["intent_info"]["confirmed"])
        self.assertEqual(self.project["visual"]["status"], "not_started")
        self.assertEqual(list((self.root / "images").iterdir()), [])

    def test_existing_project_is_not_overwritten(self):
        original = (self.root / "project.json").read_bytes()
        with self.assertRaises(FileExistsError):
            init.initialize(self.root, "replacement")
        self.assertEqual(original, (self.root / "project.json").read_bytes())

    def test_invalid_page_count_creates_nothing(self):
        for value in (0, -1, True):
            destination = Path(self.temporary.name) / f"bad-{value}"
            with self.assertRaises(ValueError):
                init.initialize(destination, page_count=value)
            self.assertFalse(destination.exists())

    def test_wrong_type_and_duplicate_intent_are_rejected(self):
        self.project["intent_info"]["direction"] = "duplicate"
        self.project["intent_info"]["data"]["page_count"] = True
        self.assertTrue(self.issues())

    def test_research_ready_without_sources_is_rejected(self):
        self.project["research"]["status"] = "ready"
        self.assertTrue(self.issues())

    def test_claim_and_page_references_must_exist(self):
        self.ready()
        self.assertFalse(self.issues())
        original = copy.deepcopy(self.project)
        self.project["research"]["claims"][0]["source_ids"] = ["missing"]
        self.assertTrue(self.issues())
        self.project = original
        self.project["script"]["pages"][0]["claim_ids"] = ["missing"]
        self.assertTrue(self.issues())

    def test_limited_research_needs_limits_and_acceptance(self):
        self.ready()
        self.project["research"]["status"] = "limited"
        self.assertTrue(self.issues())
        self.project["research"]["limits"] = ["Test-only restriction"]
        self.assertTrue(self.issues())
        self.project["research"]["user_accepted_limits"] = True
        self.assertFalse(self.issues())

    def test_failed_research_cannot_release_ready_script(self):
        self.ready()
        self.project["research"].update(status="failed", user_accepted_limits=True)
        self.assertTrue(self.issues())

    def test_planned_visual_is_distinct_from_generated(self):
        self.ready()
        self.project["visual"]["status"] = "planned"
        self.assertFalse(self.issues())
        self.project["visual"]["status"] = "generated"
        self.assertTrue(self.issues())

    def test_partial_candidates_remain_generated_pending_review(self):
        self.ready()
        self.project["visual"].update(status="generated", pages=[
            {"page_id": "p1", "candidates": ["https://example.org/test-only.png"], "review": "pending"},
            {"page_id": "p2", "candidates": [], "review": "pending"}
        ])
        self.assertFalse(self.issues())
        self.project["visual"]["pages"][1]["review"] = "passed"
        self.assertTrue(self.issues())

    def test_missing_empty_and_outside_files_rejected(self):
        self.ready()
        self.project["visual"]["assets"] = ["images/missing.png"]
        self.assertTrue(self.issues())
        (self.root / "images/empty.png").touch()
        self.project["visual"]["assets"] = ["images/empty.png"]
        self.assertTrue(self.issues())
        (self.root.parent / "outside.txt").write_text("private", encoding="utf-8")
        self.project["visual"]["assets"] = ["../outside.txt"]
        self.assertTrue(self.issues())

    def test_saved_delivery_requires_all_pages(self):
        self.ready()
        self.project["delivery"].update(status="saved", target="feishu", records=[
            {"page_id": "p1", "status": "saved", "reference": "https://example.org/record-one"}
        ])
        self.assertTrue(self.issues())
        self.project["delivery"]["status"] = "partial"
        self.assertFalse(self.issues())
        self.project["delivery"]["records"].append(
            {"page_id": "p2", "status": "saved", "reference": "https://example.org/record-two"}
        )
        self.project["delivery"]["status"] = "saved"
        self.assertFalse(self.issues())

    def test_duplicate_page_ids_rejected(self):
        self.ready()
        self.project["script"]["pages"][1]["page_id"] = "p1"
        self.assertTrue(self.issues())

    def test_package_is_standalone_reproducible_and_preserves_existing(self):
        first, second = (Path(self.temporary.name) / name for name in ("first.zip", "second.zip"))
        count, digest = packager.package(first)
        self.assertEqual((count, digest), packager.package(second))
        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            self.assertIn("medical-education-studio/SKILL.md", names)
            self.assertTrue(all(name.startswith("medical-education-studio/") for name in names))
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))
            target = Path(self.temporary.name) / "unpacked"
            archive.extractall(target)
        isolated = target / "medical-education-studio"
        isolated_init = load("isolated_init", isolated / "scripts/init_project.py")
        isolated_validator = load("isolated_validator", isolated / "scripts/validate_project.py")
        output = Path(self.temporary.name) / "isolated-project"
        isolated_init.initialize(output)
        project = json.loads((output / "project.json").read_text(encoding="utf-8"))
        self.assertFalse(isolated_validator.validate(project, output))
        with self.assertRaises(FileExistsError):
            packager.package(first)


if __name__ == "__main__":
    unittest.main()
