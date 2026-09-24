import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tooling.lib import ba_kit


ROOT = Path(__file__).resolve().parents[2]


class BaKitTests(unittest.TestCase):
    def test_manifest_resolves_existing_unique_skills(self):
        manifest = ba_kit.load_manifest(ROOT)
        skills = ba_kit.skill_composition(manifest)
        self.assertEqual(len(skills), len(set(skills)))
        for skill in skills:
            path = ROOT / skill / "SKILL.md"
            self.assertTrue(path.is_file(), skill)
            frontmatter = path.read_text(encoding="utf-8").split("---", 2)
            self.assertEqual(len(frontmatter), 3, skill)
            self.assertIn("name:", frontmatter[1], skill)
            self.assertIn("description:", frontmatter[1], skill)

    def test_agent_scope_paths_follow_native_skill_locations(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(ba_kit.resolve_target("codex", "project", project_dir=temp), Path(temp) / ".agents/skills")
            self.assertEqual(ba_kit.resolve_target("claude-code", "project", project_dir=temp), Path(temp) / ".claude/skills")
        self.assertEqual(ba_kit.resolve_target("codex", "user"), Path.home() / ".agents/skills")
        with self.assertRaisesRegex(ValueError, "requires --target"):
            ba_kit.resolve_target("generic", "project")

    def test_state_contract_rejects_missing_required_structure(self):
        valid = {
            "schema_version": 1,
            "feature": {"id": "CR-001", "title": "Appointment Scheduling"},
            "operation": "REVIEW",
            "stage": "REQUIREMENT_REVIEW",
            "artifacts": {},
            "gates": {},
            "pending": [],
            "source_of_truth": {},
            "history": [],
        }
        self.assertEqual(ba_kit.validate_state_data(valid), [])
        valid["schema_version"] = True
        self.assertIn("schema_version", " ".join(ba_kit.validate_state_data(valid)))
        valid["schema_version"] = 1
        valid["schema_version"] = 2
        self.assertIn("schema_version", " ".join(ba_kit.validate_state_data(valid)))
        valid["schema_version"] = 1
        del valid["history"]
        self.assertIn("history", " ".join(ba_kit.validate_state_data(valid)))

    def test_doctor_fails_required_and_degrades_for_missing_optional(self):
        manifest = ba_kit.load_manifest(ROOT)
        required, optional = ba_kit._skill_names(manifest)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            for skill in required:
                folder = target / skill
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(f"---\nname: {skill}\ndescription: test skill\n---\n", encoding="utf-8")
            self.assertEqual(ba_kit.doctor(ROOT, target)["status"], "DEGRADED")
            command = [sys.executable, str(ROOT / "tooling/lib/ba_kit.py"), "doctor", "ba", "--target", str(target)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("STATUS: DEGRADED", result.stdout)
            (target / required[0] / "SKILL.md").unlink()
            self.assertEqual(ba_kit.doctor(ROOT, target)["status"], "FAIL")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("STATUS: FAIL", result.stdout)

    def test_install_preflights_conflicts_before_copying(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "package"
            target = Path(temp) / "target"
            (root / "kits/ba").mkdir(parents=True)
            (root / "kits/ba/kit.yaml").write_bytes((ROOT / "kits/ba/kit.yaml").read_bytes())
            manifest = ba_kit.load_manifest(root)
            for skill in ba_kit.skill_composition(manifest):
                folder = root / skill
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text("---\nname: "+skill+"\ndescription: test\n---\n", encoding="utf-8")
            conflict = target / "drawio-skill"
            conflict.mkdir(parents=True)
            (conflict / "user-note.txt").write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "preserved"):
                ba_kit.install(root, target)
            self.assertFalse((target / "ba-workflow").exists())
            self.assertEqual((conflict / "user-note.txt").read_text(encoding="utf-8"), "preserve")

    def test_uninstall_preserves_skills_when_hash_cannot_be_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target)
            with mock.patch.object(ba_kit, "tree_hash", side_effect=ValueError("unsafe link")):
                result = ba_kit.uninstall(target)
            self.assertEqual(result["removed"], [])
            self.assertIn("codebase-discovery", result["preserved"])
            self.assertTrue((target / "codebase-discovery" / "SKILL.md").is_file())

    def test_handoff_contract_keeps_business_semantics_locked(self):
        sample = """schema_version: 1
feature:
  id: CR-001
  title: Appointment Scheduling
ba_baseline:
  status: APPROVED_FOR_ENGINEERING
  revision: ba-rev-7
authoritative_sources:
  business_rules:
    path: docs/business-rules.md
    sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  srs:
    path: docs/srs.md
    sha256: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  decisions:
    path: docs/ba-decisions.md
    sha256: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
open_items:
  blocking: []
  non_blocking: []
policy:
  downstream_may_change_business_semantics: false
  downstream_may_make_technical_design_decisions: true
next_stage:
  capability: engineering-impact-analysis
"""
        self.assertEqual(ba_kit.validate_handoff_text(sample), [])
        self.assertTrue(
            any("business semantics" in error for error in ba_kit.validate_handoff_text(
                sample.replace("downstream_may_change_business_semantics: false", "downstream_may_change_business_semantics: true")
            ))
        )
        self.assertTrue(any("blocking" in error for error in ba_kit.validate_handoff_text(
            sample.replace("blocking: []", "blocking:\n    - unresolved business question")
        )))
        self.assertEqual(ba_kit.validate_handoff_text(sample.replace("non_blocking: []", "non_blocking: [known TBD]")), [])
        self.assertTrue(any("forbidden technical field" in error for error in ba_kit.validate_handoff_text(
            sample.replace("next_stage:", "frontend_owner: someone\nnext_stage:")
        )))
        self.assertTrue(any("forbidden technical field" in error for error in ba_kit.validate_handoff_text(
            sample.replace("next_stage:", "architecture: event-driven\nnext_stage:")
        )))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources = {
                "rules.md": "approved rules",
                "srs.md": "approved srs",
                "decisions.md": "approved decisions",
            }
            valid = sample
            for section, filename, source_path, filler in (
                ("business_rules", "rules.md", "business-rules.md", "a"),
                ("srs", "srs.md", "srs.md", "b"),
                ("decisions", "decisions.md", "ba-decisions.md", "c"),
            ):
                content = sources[filename]
                (root / filename).write_text(content, encoding="utf-8")
                marker = f"  {section}:\n    path: docs/{source_path}\n    sha256: "
                valid = valid.replace(marker + filler * 64, marker + hashlib.sha256(content.encode()).hexdigest())
            valid = valid.replace("path: docs/business-rules.md", "path: rules.md")
            valid = valid.replace("path: docs/srs.md", "path: srs.md")
            valid = valid.replace("path: docs/ba-decisions.md", "path: decisions.md")
            handoff = root / "engineering-handoff.yml"
            handoff.write_text(valid, encoding="utf-8")
            self.assertEqual(ba_kit.validate_handoff_file(handoff), [])
            (root / "srs.md").write_text("changed after approval", encoding="utf-8")
            self.assertTrue(any("SHA-256 mismatch" in error for error in ba_kit.validate_handoff_file(handoff)))

    def test_handoff_block_lists_require_no_blocking_items_and_reject_design_fields(self):
        sample = """schema_version: 1
feature:
  id: CR-001
  title: Appointment Scheduling
ba_baseline:
  status: APPROVED_FOR_ENGINEERING
  revision: ba-rev-7
authoritative_sources:
  business_rules:
    path: docs/business-rules.md
    sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  srs:
    path: docs/srs.md
    sha256: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  decisions:
    path: docs/ba-decisions.md
    sha256: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
open_items:
  blocking: []
  non_blocking: []
policy:
  downstream_may_change_business_semantics: false
  downstream_may_make_technical_design_decisions: true
next_stage:
  capability: engineering-impact-analysis
"""
        self.assertEqual(ba_kit.validate_handoff_text(sample), [])  # Case A
        block_non_blocking = sample.replace(
            "  non_blocking: []",
            "  non_blocking:\n    - maximum duration remains UNKNOWN",
        )
        self.assertEqual(ba_kit.validate_handoff_text(block_non_blocking), [])  # Case B

        block_blocking = sample.replace(
            "  blocking: []",
            "  blocking:\n    - unresolved blocking issue",
        )
        self.assertTrue(any("open_items.blocking" in error for error in ba_kit.validate_handoff_text(block_blocking)))  # Case C

        with_design_field = sample.replace("next_stage:", "architecture: event-driven\nnext_stage:")
        self.assertTrue(any("forbidden technical field: architecture" in error for error in ba_kit.validate_handoff_text(with_design_field)))  # Case D

    def test_install_is_idempotent_and_uninstall_preserves_unrelated_and_edited_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            unrelated = target / "unrelated-skill"
            unrelated.mkdir(parents=True)
            (unrelated / "SKILL.md").write_text("keep me", encoding="utf-8")
            customized = target / "requirements-gap-auditor"
            customized.mkdir()
            (customized / "SKILL.md").write_text("user-owned version", encoding="utf-8")
            optional_conflict = target / "impeccable"
            optional_conflict.mkdir()
            (optional_conflict / "user-note.txt").write_text("preserve optional", encoding="utf-8")

            first = ba_kit.install(ROOT, target)
            before = ba_kit.tree_hash(target)
            second = ba_kit.install(ROOT, target)

            self.assertEqual(first["installed"], second["installed"])
            self.assertIn("impeccable", first["preserved"])
            self.assertEqual(before, ba_kit.tree_hash(target))
            self.assertEqual((customized / "SKILL.md").read_text(encoding="utf-8"), "user-owned version")
            self.assertEqual((optional_conflict / "user-note.txt").read_text(encoding="utf-8"), "preserve optional")
            state_script = target / "ba-workflow" / "scripts" / "validate-state.py"
            state_file = target / "ba-workflow" / "templates" / "workflow-state.json"
            check = subprocess.run([sys.executable, str(state_script), str(state_file)], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            handoff_script = target / "ba-workflow" / "scripts" / "validate-handoff.py"
            template = target / "ba-workflow" / "templates" / "engineering-handoff.yml"
            check = subprocess.run([sys.executable, str(handoff_script), str(template)], capture_output=True, text=True)
            self.assertEqual(check.returncode, 1)
            self.assertIn("INVALID:", check.stderr)
            self.assertNotIn("NameError", check.stderr)
            (target / ".other-kit-install.json").write_text(
                json.dumps({"kit": "other", "skills": {"verification-before-completion": {"sha256": "shared"}}}),
                encoding="utf-8",
            )
            (target / "ba-workflow" / "SKILL.md").write_text("local edit", encoding="utf-8")
            result = ba_kit.uninstall(target)

            self.assertEqual((unrelated / "SKILL.md").read_text(encoding="utf-8"), "keep me")
            self.assertEqual((customized / "SKILL.md").read_text(encoding="utf-8"), "user-owned version")
            self.assertTrue((target / "ba-workflow" / "SKILL.md").exists())
            self.assertIn("ba-workflow", result["preserved"])
            self.assertIn("verification-before-completion", result["preserved"])
            self.assertIn("codebase-discovery", result["removed"])


if __name__ == "__main__":
    unittest.main()
