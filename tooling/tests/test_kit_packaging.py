import io
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from tooling.lib import ba_kit
from tooling.lib.package import (
    PAYLOAD_DIGEST_ALGORITHM,
    build_package_authority,
    installed_tree_sha256,
    package_authority_bytes,
    package_inventory,
    payload_tree_sha256,
    payload_tree_sha256_from_inventory,
    validate_source_package_integrity,
)


ROOT = Path(__file__).resolve().parents[2]


class TestKitPackagingTests(unittest.TestCase):
    def _doctor_with_stub(self, target, source_root=ROOT):
        stub = Path(target).parent / "codex-stub.exe"
        stub.write_bytes(b"temporary Codex executable")
        with mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": str(stub)}):
            return ba_kit.doctor(source_root, target, "test")

    def test_test_manifest_resolves_explicit_runtime_only_closure(self):
        manifest = ba_kit.load_manifest(ROOT, "test")
        self.assertEqual(manifest["id"], "test")
        self.assertEqual(manifest["version"], "2.0.0-rc.5")
        self.assertEqual(manifest["capabilities"]["core"], "required")
        self.assertEqual(manifest["capabilities"]["xmind_projection"], "optional")
        self.assertEqual(manifest["capabilities"]["excel_projection"], "optional")
        self.assertEqual(manifest["integrity"]["authority"]["path"], ".test-kit/package-authority.json")
        self.assertEqual(manifest["integrity"]["payload"]["algorithm"], PAYLOAD_DIGEST_ALGORITHM)

        for skill in ba_kit.skill_composition(manifest):
            source = ROOT / manifest["skill_sources"][skill]
            self.assertTrue((source / "SKILL.md").is_file(), skill)

        sources = set()
        destinations = set()
        for item in manifest["files"]:
            self.assertTrue((ROOT / item["source"]).is_file(), item["source"])
            self.assertNotIn("benchmark/", item["source"])
            self.assertNotIn("tooling/tests/", item["source"])
            self.assertNotIn("node_modules/", item["source"])
            self.assertNotIn("__pycache__/", item["source"])
            sources.add(item["source"])
            destinations.add(item["destination"])
        self.assertEqual(len(destinations), len(manifest["files"]))
        self.assertIn("tooling/lib/test_kit_v1.py", sources)
        self.assertIn("tooling/lib/test_kit_policy.py", sources)
        self.assertIn("tooling/lib/test_kit_v1_cases.py", sources)
        self.assertIn("tooling/lib/codex_cli.py", sources)
        self.assertIn("ba-workflow/scripts/contracts.py", sources)

    def test_manifest_rejects_asset_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "skill"
            source.mkdir()
            (source / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
            manifest_dir = root / "kits/demo"
            manifest_dir.mkdir(parents=True)
            manifest = {
                "schema_version": 1,
                "id": "demo",
                "name": "Demo",
                "version": "1.0.0",
                "workflow": {"skill": "demo"},
                "core": [],
                "skills": {"required": [], "optional": []},
                "files": [{"source": "skill/SKILL.md", "destination": "../outside", "classification": "runtime"}],
            }
            (manifest_dir / "kit.yaml").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "destination"):
                ba_kit.load_manifest(root, "demo")

    def test_integrity_manifest_requires_explicit_canonical_definition_and_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_dir = root / "kits/demo"
            manifest_dir.mkdir(parents=True)
            path = manifest_dir / "kit.yaml"
            manifest = _demo_manifest("1.0.0")
            manifest["files"].extend([
                {"source": "kits/demo/kit.yaml", "destination": ".demo-kit/kit.yaml", "classification": "PACKAGE_MANIFEST"},
                {"source": "kits/demo/package-authority.json", "destination": ".demo/package-authority.json", "classification": "PACKAGE_AUTHORITY"},
            ])
            manifest["integrity"] = {
                "authority": {"path": ".demo/package-authority.json", "sha256": "a" * 64},
                "payload": {"algorithm": PAYLOAD_DIGEST_ALGORITHM, "sha256": "b" * 64},
            }
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(ba_kit.load_manifest(root, "demo")["integrity"]["payload"]["algorithm"], PAYLOAD_DIGEST_ALGORITHM)

            invalid_cases = []
            invalid = json.loads(json.dumps(manifest))
            invalid["files"] = [item for item in invalid["files"] if item["destination"] != ".demo-kit/kit.yaml"]
            invalid_cases.append(invalid)
            invalid = json.loads(json.dumps(manifest))
            invalid["integrity"]["payload"]["algorithm"] = "UNVERSIONED"
            invalid_cases.append(invalid)
            invalid = json.loads(json.dumps(manifest))
            invalid["integrity"]["authority"]["sha256"] = "not-a-hash"
            invalid_cases.append(invalid)
            for invalid in invalid_cases:
                with self.subTest(invalid=invalid):
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        ba_kit.load_manifest(root, "demo")

    def test_manifest_validates_supported_scopes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_dir = root / "kits/demo"
            manifest_dir.mkdir(parents=True)
            manifest_path = manifest_dir / "kit.yaml"
            manifest = _demo_manifest("1.0.0")
            manifest["scopes"] = ["project"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(ba_kit.load_manifest(root, "demo")["scopes"], ["project"])

            for scopes in (["project", "project"], ["global"], []):
                manifest["scopes"] = scopes
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.subTest(scopes=scopes), self.assertRaisesRegex(ValueError, "manifest scopes"):
                    ba_kit.load_manifest(root, "demo")

    def test_missing_python_and_unsupported_agent_fail_before_install(self):
        errors = io.StringIO()
        with mock.patch.object(ba_kit.sys, "version_info", (3, 9)), redirect_stderr(errors):
            result = ba_kit.main(["install", "test", "--agent", "generic", "--target", "unused"])
        self.assertEqual(result, 2)
        self.assertIn("Python 3.10+", errors.getvalue())

        errors = io.StringIO()
        with redirect_stderr(errors):
            result = ba_kit.main(["install", "test", "--agent", "claude-code", "--target", "unused"])
        self.assertEqual(result, 2)
        self.assertIn("supports these agents: codex", errors.getvalue())

        errors = io.StringIO()
        with redirect_stderr(errors):
            result = ba_kit.main(["install", "test", "--agent", "codex", "--scope", "user"])
        self.assertEqual(result, 2)
        self.assertIn("supports these scopes: project", errors.getvalue())

    def test_install_record_compatibility_is_explicit_and_positive(self):
        digest = "a" * 64
        legacy_ba = {
            "schema_version": 1,
            "kit": "ba",
            "version": "1.0.0-rc.1",
            "skills": {"ba-workflow": {"sha256": digest}},
        }
        modern_ba = {
            **legacy_ba,
            "files": {},
            "managed_files": {
                "ba-workflow/SKILL.md": {"sha256": digest, "classification": "REQUIRED_SKILL"}
            },
            "managed_file_count": 1,
        }
        modern_test = {
            "schema_version": 1,
            "kit": "test",
            "version": "1.0.0",
            "skills": {"test-kit": {"sha256": digest}},
            "files": {".test-kit/kit.yaml": {"sha256": digest, "classification": "PACKAGE_MANIFEST"}},
            "managed_files": {
                "test-kit/SKILL.md": {"sha256": digest, "classification": "REQUIRED_SKILL"},
                ".test-kit/kit.yaml": {"sha256": digest, "classification": "PACKAGE_MANIFEST"},
            },
            "managed_file_count": 2,
        }
        record_path = Path("install-record.json")
        ba_kit._validate_install_record(legacy_ba, record_path, "ba")
        ba_kit._validate_install_record(modern_ba, record_path, "ba")
        ba_kit._validate_install_record(modern_test, record_path, "test")

        for invalid in (
            {**modern_ba, "files": []},
            {**modern_ba, "managed_files": []},
            {**modern_ba, "managed_files": {}},
            {**modern_ba, "schema_version": 2},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                ba_kit._validate_install_record(invalid, record_path, "ba")

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / ".ba-kit-install.json").write_text(json.dumps(legacy_ba), encoding="utf-8")
            self.assertFalse(
                ba_kit._another_kit_owns(
                    target, "files", ".test-kit/tooling/lib/test_kit_v1.py", target / ".test-kit-install.json"
                )
            )

    def test_project_install_bootstraps_tea_config_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            target = project / ".agents/skills"

            first = ba_kit.install(ROOT, target, "test")
            config = project / "_bmad/tea/config.yaml"

            self.assertEqual(first["tea_project_config"]["status"], "CREATED")
            self.assertTrue(config.is_file())
            text = config.read_text(encoding="utf-8")
            self.assertIn("communication_language: Vietnamese", text)
            self.assertIn("document_output_language: Vietnamese", text)
            self.assertIn("output_folder: .test-kit/runtime", text)
            self.assertIn("test_artifacts: .test-kit/runtime", text)
            self.assertTrue((project / ".test-kit/runtime").is_dir())
            self.assertNotIn(str(project.resolve()).replace("\\\\", "/"), text)

            custom = text.replace("user_name: Tester", "user_name: Project Tester")
            config.write_text(custom, encoding="utf-8")
            second = ba_kit.install(ROOT, target, "test")

            self.assertEqual(second["tea_project_config"]["status"], "PRESERVED")
            self.assertEqual(config.read_text(encoding="utf-8"), custom)

    def test_doctor_rejects_run_bound_project_tea_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            target = project / ".agents/skills"
            ba_kit.install(ROOT, target, "test")
            config = project / "_bmad/tea/config.yaml"
            text = config.read_text(encoding="utf-8").replace(
                ".test-kit/runtime",
                "test-runs/CR-DEMO-001/design-20261002-02/raw-output",
            )
            config.write_text(text, encoding="utf-8")

            report = self._doctor_with_stub(target)
            self.assertEqual(report["status"], "FAIL", report["checks"])
            self.assertTrue(
                any(
                    name == "TEA_PROJECT_CONFIG" and not ok and "TEA_PROJECT_CONFIG_RUN_BOUND" in detail
                    for name, ok, _, detail in report["checks"]
                )
            )

    def test_doctor_fails_when_project_tea_config_is_missing_or_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            target = project / ".agents/skills"
            ba_kit.install(ROOT, target, "test")
            config = project / "_bmad/tea/config.yaml"
            config.unlink()

            report = self._doctor_with_stub(target)
            self.assertEqual(report["status"], "FAIL", report["checks"])
            self.assertTrue(
                any(
                    name == "TEA_PROJECT_CONFIG" and not ok and "TEA_PROJECT_CONFIG_MISSING" in detail
                    for name, ok, _, detail in report["checks"]
                )
            )

            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text("user_name: Tester\n", encoding="utf-8")
            report = self._doctor_with_stub(target)
            self.assertEqual(report["status"], "FAIL", report["checks"])
            self.assertTrue(
                any(
                    name == "TEA_PROJECT_CONFIG" and not ok and "TEA_PROJECT_CONFIG_INVALID" in detail
                    for name, ok, _, detail in report["checks"]
                )
            )

    def test_test_install_records_every_skill_and_runtime_file_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            manifest = ba_kit.load_manifest(ROOT, "test")
            record = json.loads((target / ".test-kit-install.json").read_text(encoding="utf-8"))
            managed = record["managed_files"]
            skill_file = "bmad-testarch-test-design/checklist.md"
            runtime_file = ".test-kit/tooling/lib/test_kit_v1.py"

            self.assertEqual(record["kit"], "test")
            self.assertEqual(record["version"], manifest["version"])
            self.assertEqual(record["manifest_schema_version"], manifest["schema_version"])
            self.assertEqual(record["source_repository"], manifest["install_metadata"]["source_repository"])
            self.assertRegex(record["source_revision"], r"^[0-9a-f]{40}$")
            self.assertEqual(record["capabilities"], manifest["capabilities"])
            self.assertEqual(record["managed_file_count"], len(managed))
            pinned = {item["id"]: item["version"] for item in record["pinned_dependencies"]}
            self.assertEqual(pinned["bmad-testarch-test-design"], "1f53e9095061ab66f3c35abd9b98baf0f50cf8fe")
            self.assertEqual(pinned["create-test-cases"], "e6cdd774f66ce9d45ea5904101a96203e3a37581")
            self.assertEqual(
                managed[skill_file]["sha256"],
                hashlib.sha256((target / skill_file).read_bytes()).hexdigest(),
            )
            self.assertEqual(managed[skill_file]["classification"], "REQUIRED_SKILL")
            self.assertEqual(
                managed[runtime_file]["sha256"],
                hashlib.sha256((target / runtime_file).read_bytes()).hexdigest(),
            )
            self.assertEqual(managed[runtime_file]["classification"], "CORE_RUNTIME")
            self.assertEqual(record["payload_digest_algorithm"], PAYLOAD_DIGEST_ALGORITHM)
            self.assertRegex(record["payload_tree_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(record["pinned_dependencies"], manifest["dependencies"])
            self.assertEqual(record["payload_tree_sha256"], payload_tree_sha256(ROOT, manifest))
            authority_path = target / ".test-kit/package-authority.json"
            authority = json.loads(authority_path.read_text(encoding="utf-8"))
            self.assertEqual(authority["kit_id"], "test")
            self.assertEqual(authority["kit_version"], manifest["version"])
            self.assertEqual(authority["manifest_schema_version"], manifest["schema_version"])
            self.assertEqual(authority["managed_file_count"], len(managed))
            self.assertEqual({item["path"] for item in authority["managed_files"]}, set(managed))
            self.assertEqual(record["managed_files"], {item["path"]: {"sha256": item["sha256"], "classification": item["classification"]} for item in authority["managed_files"]})
            self.assertEqual(authority["payload_tree_sha256"], record["payload_tree_sha256"])
            self.assertEqual(authority["payload_digest_algorithm"], manifest["integrity"]["payload"]["algorithm"])
            self.assertEqual(payload_tree_sha256_from_inventory(authority["managed_files"]), authority["payload_tree_sha256"])
            authority_hash = hashlib.sha256(authority_path.read_bytes()).hexdigest()
            self.assertEqual(authority_hash, manifest["integrity"]["authority"]["sha256"])
            report = self._doctor_with_stub(target)
            self.assertEqual(report["status"], "READY", report["checks"])
            payload = Path(temp) / "payload-only"
            for item in authority["managed_files"]:
                destination = payload / item["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(target / item["path"], destination)
            self.assertEqual(record["payload_tree_sha256"], installed_tree_sha256(payload))

    def test_clean_installs_generate_identical_package_authority_and_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            trees = []
            inventories = []
            manifest = ba_kit.load_manifest(ROOT, "test")
            for name in ("first", "second"):
                target = Path(temp) / name
                ba_kit.install(ROOT, target, "test")
                trees.append((target / ".test-kit/package-authority.json").read_bytes())
                inventories.append(package_inventory(target, source_root=ROOT, manifest=manifest))
                if name == "first":
                    first_tree_digest = installed_tree_sha256(target)
                else:
                    self.assertEqual(installed_tree_sha256(target), first_tree_digest)
            self.assertEqual(trees[0], trees[1])
            self.assertEqual(inventories[0], inventories[1])

    def test_installer_script_entrypoint_writes_package_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            result = subprocess.run(
                [sys.executable, str(ROOT / "tooling/lib/ba_kit.py"), "install", "test", "--agent", "generic", "--target", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            record = json.loads((target / ".test-kit-install.json").read_text(encoding="utf-8"))
            self.assertEqual(record["payload_digest_algorithm"], PAYLOAD_DIGEST_ALGORITHM)
            self.assertRegex(record["payload_tree_sha256"], r"^[0-9a-f]{64}$")
            codex_stub = Path(temp) / "codex-stub.exe"
            codex_stub.write_bytes(b"stub")
            env = os.environ.copy()
            env["TEST_KIT_CODEX_COMMAND"] = str(codex_stub)
            doctor = subprocess.run(
                [sys.executable, str(ROOT / "tooling/lib/ba_kit.py"), "doctor", "test", "--agent", "generic", "--target", str(target)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("STATUS: READY", doctor.stdout)

    def test_doctor_reports_modified_skill_file_and_reinstall_keeps_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            record_path = target / ".test-kit-install.json"
            record_before = json.loads(record_path.read_text(encoding="utf-8"))
            relative = "bmad-testarch-test-design/checklist.md"
            expected_hash = record_before["managed_files"][relative]["sha256"]
            payload_digest = record_before["payload_tree_sha256"]
            edited = target / relative
            edited.write_bytes(edited.read_bytes() + b"\nlocal change\n")

            report = ba_kit.doctor(ROOT, target, "test")
            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(name == "MODIFIED_MANAGED_FILE" and relative in detail for name, _, _, detail in report["checks"]))

            result = ba_kit.install(ROOT, target, "test")
            self.assertIn("bmad-testarch-test-design", result["preserved"])
            self.assertIn("bmad-testarch-test-design", result["conflicts"])
            record_after = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record_after["managed_files"][relative]["sha256"], expected_hash)
            self.assertEqual(record_after["payload_tree_sha256"], payload_digest)
            self.assertIn(b"local change", edited.read_bytes())
            report = ba_kit.doctor(ROOT, target, "test")
            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(name == "MODIFIED_MANAGED_FILE" and relative in detail for name, _, _, detail in report["checks"]))

    def test_doctor_detects_missing_and_corrupt_managed_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            relative = ".test-kit/tooling/lib/test_kit_v1.py"
            (target / relative).unlink()
            report = ba_kit.doctor(ROOT, target, "test")
            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(name == "MISSING_MANAGED_FILE" and relative in detail for name, _, _, detail in report["checks"]))

        for corrupt in ("hash", "missing_digest", "unsupported_algorithm"):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / "skills"
                ba_kit.install(ROOT, target, "test")
                record_path = target / ".test-kit-install.json"
                record = json.loads(record_path.read_text(encoding="utf-8"))
                if corrupt == "hash":
                    record["managed_files"]["test-kit/SKILL.md"]["sha256"] = "invalid"
                elif corrupt == "missing_digest":
                    record.pop("payload_tree_sha256")
                else:
                    record["payload_digest_algorithm"] = "UNKNOWN_TREE_V9"
                record_path.write_text(json.dumps(record), encoding="utf-8")
                report = ba_kit.doctor(ROOT, target, "test")
                self.assertNotEqual(report["status"], "READY")
                self.assertTrue(any(name == "PACKAGE_METADATA_INVALID" for name, _, _, _ in report["checks"]))

    def test_package_authority_rejects_incomplete_or_mutated_install_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            record_path = target / ".test-kit-install.json"
            authority_path = target / ".test-kit/package-authority.json"
            original_record = json.loads(record_path.read_text(encoding="utf-8"))
            original_authority = json.loads(authority_path.read_text(encoding="utf-8"))
            tea_file = "bmad-testarch-test-design/checklist.md"
            runtime_file = ".test-kit/README.md"

            mutations = {
                "omit_tea_and_decrement": lambda record: (record["managed_files"].pop(tea_file), record.update(managed_file_count=record["managed_file_count"] - 1)),
                "omit_runtime_and_decrement": lambda record: (record["managed_files"].pop(runtime_file), record.update(managed_file_count=record["managed_file_count"] - 1)),
                "omit_without_count_change": lambda record: record["managed_files"].pop(tea_file),
                "add_unknown": lambda record: (record["managed_files"].update({".unknown/user.txt": {"sha256": "a" * 64, "classification": "CORE_RUNTIME"}}), record.update(managed_file_count=record["managed_file_count"] + 1)),
                "classification": lambda record: record["managed_files"][tea_file].update(classification="CORE_RUNTIME"),
                "expected_hash": lambda record: record["managed_files"][tea_file].update(sha256="0" * 64),
                "valid_but_wrong_package_digest": lambda record: record.update(payload_tree_sha256="f" * 64),
                "unsupported_digest_algorithm": lambda record: record.update(payload_digest_algorithm="OTHER_V1"),
                "missing_digest": lambda record: record.pop("payload_tree_sha256"),
            }
            for name, mutate in mutations.items():
                with self.subTest(mutation=name):
                    record = json.loads(json.dumps(original_record))
                    mutate(record)
                    record_path.write_text(json.dumps(record), encoding="utf-8")
                    report = self._doctor_with_stub(target)
                    self.assertNotEqual(report["status"], "READY")
                    self.assertTrue(any(label == "PACKAGE_METADATA_INVALID" and not ok for label, ok, _, _ in report["checks"]))

            compact = json.dumps(original_record, separators=(",", ":"))
            duplicate = json.dumps(tea_file) + ":" + json.dumps(original_record["managed_files"][tea_file], separators=(",", ":"))
            record_path.write_text(compact.replace(duplicate, duplicate + "," + duplicate, 1), encoding="utf-8")
            report = self._doctor_with_stub(target)
            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(label == "PACKAGE_METADATA_INVALID" and not ok for label, ok, _, _ in report["checks"]))

            reordered = json.loads(json.dumps(original_record))
            reordered["managed_files"] = dict(reversed(list(reordered["managed_files"].items())))
            record_path.write_text(json.dumps(reordered), encoding="utf-8")
            self.assertEqual(self._doctor_with_stub(target)["status"], "READY")

            incomplete_authority = json.loads(json.dumps(original_authority))
            incomplete_authority["managed_files"] = [entry for entry in incomplete_authority["managed_files"] if entry["path"] != tea_file]
            incomplete_authority["managed_file_count"] -= 1
            incomplete_authority["payload_tree_sha256"] = payload_tree_sha256_from_inventory(incomplete_authority["managed_files"])
            authority_path.write_text(json.dumps(incomplete_authority), encoding="utf-8")
            report = self._doctor_with_stub(target)
            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(label == "PACKAGE_METADATA_INVALID" and not ok for label, ok, _, _ in report["checks"]))

            authority_path.write_text(json.dumps(original_authority), encoding="utf-8")
            for name, mutate in (
                ("malformed_digest", lambda authority: authority.update(payload_tree_sha256="not-a-sha256")),
                ("valid_but_wrong_digest", lambda authority: authority.update(payload_tree_sha256="f" * 64)),
                ("unsupported_algorithm", lambda authority: authority.update(payload_digest_algorithm="OTHER_V1")),
                ("duplicate_path", lambda authority: (authority["managed_files"].append(authority["managed_files"][0]), authority.update(managed_file_count=authority["managed_file_count"] + 1))),
                ("invalid_classification", lambda authority: authority["managed_files"][0].update(classification="UNKNOWN")),
            ):
                with self.subTest(authority_mutation=name):
                    authority = json.loads(json.dumps(original_authority))
                    mutate(authority)
                    authority_path.write_text(json.dumps(authority), encoding="utf-8")
                    report = self._doctor_with_stub(target)
                    self.assertNotEqual(report["status"], "READY")
                    self.assertTrue(any(label == "PACKAGE_METADATA_INVALID" and not ok for label, ok, _, _ in report["checks"]))

    def test_authoritative_file_hash_cannot_be_replaced_with_local_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            relative = "bmad-testarch-test-design/checklist.md"
            edited = target / relative
            edited.write_bytes(edited.read_bytes() + b"local mutation\n")
            record_path = target / ".test-kit-install.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["managed_files"][relative]["sha256"] = hashlib.sha256(edited.read_bytes()).hexdigest()
            record_path.write_text(json.dumps(record), encoding="utf-8")

            report = self._doctor_with_stub(target)

            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(label == "PACKAGE_METADATA_INVALID" and not ok for label, ok, _, _ in report["checks"]))
            self.assertTrue(any(label == "MODIFIED_MANAGED_FILE" and relative in detail for label, _, _, detail in report["checks"]))

    def test_doctor_uses_installed_package_definition_and_binds_both_pins(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            definition_path = target / ".test-kit/kit.yaml"
            authority_path = target / ".test-kit/package-authority.json"
            definition = json.loads(definition_path.read_text(encoding="utf-8"))
            authority, authority_bytes, authority_sha = validate_source_package_integrity(ROOT, ba_kit.load_manifest(ROOT, "test"))

            self.assertEqual(authority_sha, definition["integrity"]["authority"]["sha256"])
            self.assertEqual(authority["payload_tree_sha256"], definition["integrity"]["payload"]["sha256"])
            absent_source = Path(temp) / "source-is-not-needed"
            self.assertEqual(self._doctor_with_stub(target, absent_source)["status"], "READY")

            original_definition = definition_path.read_bytes()
            for pin in ("authority", "payload"):
                changed = json.loads(original_definition)
                field = "sha256"
                changed["integrity"][pin][field] = "f" * 64
                definition_path.write_text(json.dumps(changed), encoding="utf-8")
                report = self._doctor_with_stub(target, absent_source)
                self.assertNotEqual(report["status"], "READY")
                self.assertTrue(any(label == "PACKAGE_AUTHORITY_INVALID" and not ok for label, ok, _, _ in report["checks"]))
                definition_path.write_bytes(original_definition)

            replacement = json.loads(authority_bytes)
            replacement["managed_files"] = list(reversed(replacement["managed_files"]))
            authority_path.write_bytes(package_authority_bytes(replacement))
            report = self._doctor_with_stub(target, absent_source)
            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(label == "PACKAGE_AUTHORITY_INVALID" and "SHA-256" in detail for label, _, _, detail in report["checks"]))
            authority_path.write_bytes(authority_bytes)

    def test_truncated_authority_is_rejected_even_when_internally_consistent(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            authority_path = target / ".test-kit/package-authority.json"
            original = json.loads(authority_path.read_text(encoding="utf-8"))
            truncated = json.loads(json.dumps(original))
            truncated["managed_files"] = [row for row in truncated["managed_files"] if row["path"] != "bmad-testarch-test-design/checklist.md"]
            truncated["managed_file_count"] -= 1
            truncated["payload_tree_sha256"] = payload_tree_sha256_from_inventory(truncated["managed_files"])
            authority_path.write_bytes(package_authority_bytes(truncated))

            report = self._doctor_with_stub(target)

            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(label == "PACKAGE_AUTHORITY_INVALID" and not ok for label, ok, _, _ in report["checks"]))

    def test_exact_coordinated_authority_record_and_runtime_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            definition_path = target / ".test-kit/kit.yaml"
            definition_before = definition_path.read_bytes()
            authority_path = target / ".test-kit/package-authority.json"
            record_path = target / ".test-kit-install.json"
            skill_file = target / "bmad-testarch-test-design/checklist.md"
            skill_file.unlink()

            authority = json.loads(authority_path.read_text(encoding="utf-8"))
            relative = "bmad-testarch-test-design/checklist.md"
            authority["managed_files"] = [row for row in authority["managed_files"] if row["path"] != relative]
            authority["managed_file_count"] -= 1
            authority["payload_tree_sha256"] = payload_tree_sha256_from_inventory(authority["managed_files"])
            authority_bytes = package_authority_bytes(authority)
            authority_path.write_bytes(authority_bytes)

            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["managed_files"].pop(relative)
            record["managed_file_count"] -= 1
            record["payload_tree_sha256"] = authority["payload_tree_sha256"]
            record["files"][".test-kit/package-authority.json"]["sha256"] = hashlib.sha256(authority_bytes).hexdigest()
            record["skills"]["bmad-testarch-test-design"]["sha256"] = ba_kit.tree_hash(target / "bmad-testarch-test-design")
            record_path.write_text(json.dumps(record), encoding="utf-8")

            report = self._doctor_with_stub(target)

            self.assertNotEqual(report["status"], "READY")
            self.assertEqual(definition_path.read_bytes(), definition_before)
            self.assertTrue(any(label == "PACKAGE_AUTHORITY_INVALID" and "SHA-256" in detail for label, _, _, detail in report["checks"]))

    def test_source_manifest_pin_mismatch_blocks_install_before_target_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            skill_source = root / "kits/demo/skills/demo"
            skill_source.mkdir(parents=True)
            (skill_source / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
            (root / "runtime.py").write_text("runtime\n", encoding="utf-8")
            manifest = _demo_manifest("1.0.0")
            manifest["files"].extend([
                {"source": "kits/demo/kit.yaml", "destination": ".demo-kit/kit.yaml", "classification": "PACKAGE_MANIFEST"},
                {"source": "kits/demo/package-authority.json", "destination": ".demo/package-authority.json", "classification": "PACKAGE_AUTHORITY"},
            ])
            manifest["integrity"] = {
                "authority": {"path": ".demo/package-authority.json", "sha256": "0" * 64},
                "payload": {"algorithm": PAYLOAD_DIGEST_ALGORITHM, "sha256": "0" * 64},
            }
            _seal_integrity_package(root, manifest)
            manifest["integrity"]["authority"]["sha256"] = "f" * 64
            (root / "kits/demo/kit.yaml").write_text(json.dumps(manifest), encoding="utf-8")
            target = Path(temp) / "fresh-target"

            with self.assertRaisesRegex(ValueError, "manifest pin"):
                ba_kit.install(root, target, "demo")

            self.assertFalse(target.exists())

    def test_authority_definition_and_record_publication_failures_roll_back_upgrade(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            target = Path(temp) / "project/.agents/skills"
            skill_source = root / "kits/demo/skills/demo"
            skill_source.mkdir(parents=True)
            skill_path = skill_source / "SKILL.md"
            skill_path.write_text("---\nname: demo\ndescription: v1\n---\n", encoding="utf-8")
            runtime_source = root / "runtime.py"
            runtime_source.write_text("runtime-v1\n", encoding="utf-8")
            manifest = _demo_manifest("1.0.0")
            manifest["files"].extend([
                {"source": "kits/demo/kit.yaml", "destination": ".demo-kit/kit.yaml", "classification": "PACKAGE_MANIFEST"},
                {"source": "kits/demo/package-authority.json", "destination": ".demo/package-authority.json", "classification": "PACKAGE_AUTHORITY"},
            ])
            manifest["integrity"] = {
                "authority": {"path": ".demo/package-authority.json", "sha256": "0" * 64},
                "payload": {"algorithm": PAYLOAD_DIGEST_ALGORITHM, "sha256": "0" * 64},
            }
            manifest_path = root / "kits/demo/kit.yaml"
            authority_source = root / "kits/demo/package-authority.json"
            _seal_integrity_package(root, manifest)
            ba_kit.install(root, target, "demo")
            record_path = target / ".demo-kit-install.json"
            authority_path = target / ".demo/package-authority.json"
            definition_path = target / ".demo-kit/kit.yaml"
            installed_runtime = target / ".demo/runtime.py"
            installed_skill = target / "demo/SKILL.md"
            prior = {path: path.read_bytes() for path in (record_path, authority_path, definition_path, installed_runtime, installed_skill)}

            manifest["version"] = "2.0.0"
            runtime_source.write_text("runtime-v2\n", encoding="utf-8")
            skill_path.write_text("---\nname: demo\ndescription: v2\n---\n", encoding="utf-8")
            _seal_integrity_package(root, manifest)

            real_replace = os.replace
            for destination, label in ((authority_path, "authority"), (definition_path, "definition")):
                def injected_replace(source, dest, expected=destination, original=real_replace):
                    if Path(dest).resolve() == expected.resolve() and Path(source).parent.name == "new":
                        raise OSError(f"simulated {label} publication failure")
                    return original(source, dest)

                with mock.patch.object(ba_kit.os, "replace", side_effect=injected_replace):
                    with self.assertRaisesRegex(OSError, f"{label} publication"):
                        ba_kit.install(root, target, "demo")
                self.assertEqual({path: path.read_bytes() for path in prior}, prior)

            with mock.patch.object(ba_kit, "_write_json", side_effect=OSError("simulated install record publication failure")):
                with self.assertRaisesRegex(OSError, "install record publication"):
                    ba_kit.install(root, target, "demo")
            self.assertEqual({path: path.read_bytes() for path in prior}, prior)
            manifest["version"] = "1.0.0"
            runtime_source.write_text("runtime-v1\n", encoding="utf-8")
            skill_path.write_text("---\nname: demo\ndescription: v1\n---\n", encoding="utf-8")
            _seal_integrity_package(root, manifest)
            report = ba_kit.doctor(root, target, "demo")
            self.assertEqual(report["status"], "READY", report["checks"])

    def test_doctor_distinguishes_required_and_optional_missing_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            codex_stub = Path(temp) / "codex-stub.exe"
            codex_stub.write_bytes(b"stub")
            with (
                mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": str(codex_stub), "PATH": ""}),
                mock.patch.object(ba_kit.shutil, "which", return_value=None),
                mock.patch("importlib.util.find_spec", return_value=None),
            ):
                report = ba_kit.doctor(ROOT, target, "test")
            self.assertEqual(report["status"], "READY")
            self.assertTrue(any(name == "DEPENDENCY_MISSING" and kind == "dependency" for name, _, kind, _ in report["checks"]))

            with (
                mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": "", "PATH": ""}),
                mock.patch.object(ba_kit.shutil, "which", return_value=None),
            ):
                report = ba_kit.doctor(ROOT, target, "test")
            # Audit R3.2: same-session production core has no nested Codex dependency.
            self.assertEqual(report["status"], "READY")
            self.assertFalse(any(name == "DEPENDENCY_MISSING" and "Codex" in detail for name, _, _, detail in report["checks"]))

    def test_ba_and_test_ownership_is_independent_in_both_uninstall_orders(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            target.mkdir()
            unrelated = target / "user-owned.txt"
            unrelated.write_text("keep", encoding="utf-8")
            ba_kit.install(ROOT, target, "ba")
            ba_kit.install(ROOT, target, "test")
            ba_record = json.loads((target / ".ba-kit-install.json").read_text(encoding="utf-8"))
            test_record = json.loads((target / ".test-kit-install.json").read_text(encoding="utf-8"))
            ba_paths = set(ba_record["managed_files"])
            test_paths = set(test_record["managed_files"])
            self.assertIn("ba-workflow/SKILL.md", ba_paths)
            self.assertIn(".test-kit/tooling/lib/test_kit_v1.py", test_paths)
            self.assertFalse(ba_paths & test_paths)  # No shared files are declared.
            self.assertNotIn("user-owned.txt", ba_paths | test_paths)  # UNMANAGED.

            codex_stub = Path(temp) / "codex-stub.exe"
            codex_stub.write_bytes(b"stub")
            with mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": str(codex_stub)}):
                self.assertEqual(ba_kit.doctor(ROOT, target, "ba")["status"], "READY")
                self.assertEqual(ba_kit.doctor(ROOT, target, "test")["status"], "READY")
            result = ba_kit.uninstall(target, "test")
            self.assertIn(".test-kit/tooling/lib/test_kit_v1.py", result["removed"])
            self.assertFalse((target / ".test-kit-install.json").exists())
            self.assertTrue((target / ".ba-kit-install.json").exists())
            self.assertTrue((target / "ba-workflow/SKILL.md").is_file())
            self.assertEqual(ba_kit.doctor(ROOT, target, "ba")["status"], "READY")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            target.mkdir()
            unrelated = target / "user-owned.txt"
            unrelated.write_text("keep", encoding="utf-8")

            ba_kit.install(ROOT, target, "ba")
            ba_record_path = target / ".ba-kit-install.json"
            ba_record = json.loads(ba_record_path.read_text(encoding="utf-8"))
            # Simulate a valid pre-generalization BA record with no file ownership section.
            ba_record.pop("files", None)
            ba_record.pop("managed_files", None)
            ba_record.pop("managed_file_count", None)
            ba_record_path.write_text(json.dumps(ba_record), encoding="utf-8")
            ba_kit.install(ROOT, target, "test")

            test_record_path = target / ".test-kit-install.json"
            test_record = json.loads(test_record_path.read_text(encoding="utf-8"))
            ba_paths = set(ba_record["skills"])
            test_paths = set(test_record["skills"]) | set(test_record["files"])
            self.assertIn("ba-workflow", ba_paths)
            self.assertIn(".test-kit/tooling/lib/test_kit_v1.py", test_paths)
            self.assertFalse(ba_paths & test_paths)
            codex_stub = Path(temp) / "codex-stub.exe"
            codex_stub.write_bytes(b"stub")
            with mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": str(codex_stub)}):
                self.assertEqual(ba_kit.doctor(ROOT, target, "ba")["status"], "READY")
                self.assertEqual(ba_kit.doctor(ROOT, target, "test")["status"], "READY")

            result = ba_kit.uninstall(target, "test")
            self.assertIn(".test-kit/tooling/lib/test_kit_v1.py", result["removed"])
            self.assertFalse(test_record_path.exists())
            self.assertTrue(ba_record_path.exists())
            self.assertTrue((target / "ba-workflow/SKILL.md").is_file())
            self.assertEqual(ba_kit.doctor(ROOT, target, "ba")["status"], "READY")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            ba_kit.install(ROOT, target, "ba")
            ba_record_path = target / ".ba-kit-install.json"
            test_record_path = target / ".test-kit-install.json"
            codex_stub = Path(temp) / "codex-stub.exe"
            codex_stub.write_bytes(b"stub")
            with mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": str(codex_stub)}):
                self.assertEqual(ba_kit.doctor(ROOT, target, "ba")["status"], "READY")
                self.assertEqual(ba_kit.doctor(ROOT, target, "test")["status"], "READY")

            ba_kit.uninstall(target, "ba")
            self.assertFalse(ba_record_path.exists())
            self.assertTrue(test_record_path.exists())
            self.assertTrue((target / ".test-kit/tooling/lib/test_kit_v1.py").is_file())
            with mock.patch.dict(os.environ, {"TEST_KIT_CODEX_COMMAND": str(codex_stub)}):
                self.assertEqual(ba_kit.doctor(ROOT, target, "test")["status"], "READY")

    def test_standalone_test_uninstall_removes_managed_assets_and_keeps_unrelated_file(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            target.mkdir()
            unrelated = target / "user-owned.txt"
            unrelated.write_text("keep", encoding="utf-8")
            ba_kit.install(ROOT, target, "test")

            result = ba_kit.uninstall(target, "test")

            self.assertFalse((target / ".test-kit-install.json").exists())
            self.assertFalse((target / ".test-kit").exists())
            self.assertFalse((target / "bmad-testarch-test-design").exists())
            self.assertFalse((target / "create-test-cases").exists())
            self.assertFalse((target / "test-kit").exists())
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")
            self.assertTrue(result["removed"])

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "test")
            edited = target / "bmad-testarch-test-design/checklist.md"
            edited.write_bytes(edited.read_bytes() + b"\nlocal change\n")
            result = ba_kit.uninstall(target, "test")
            self.assertIn("bmad-testarch-test-design", result["preserved"])
            self.assertTrue(edited.is_file())
            self.assertTrue((target / ".test-kit-install.json").is_file())
            self.assertFalse((target / ".test-kit").exists())

    def test_ba_doctor_detects_modification_in_modern_install_record(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            ba_kit.install(ROOT, target, "ba")
            relative = "ba-workflow/SKILL.md"
            managed = target / relative
            managed.write_text(managed.read_text(encoding="utf-8") + "\nlocal change\n", encoding="utf-8")

            report = ba_kit.doctor(ROOT, target, "ba")

            self.assertNotEqual(report["status"], "READY")
            self.assertTrue(any(name == "MODIFIED_MANAGED_FILE" and relative in detail for name, _, _, detail in report["checks"]))
            before = managed.read_bytes()
            result = ba_kit.install(ROOT, target, "ba")
            self.assertIn("ba-workflow", result["conflicts"])
            self.assertEqual(managed.read_bytes(), before)
            self.assertNotEqual(ba_kit.doctor(ROOT, target, "ba")["status"], "READY")
            result = ba_kit.uninstall(target, "ba")
            self.assertIn("ba-workflow", result["preserved"])

    def test_fresh_install_reinstall_upgrade_and_uninstall_manage_only_owned_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            target = Path(temp) / "project/.agents/skills"
            skill_source = root / "kits/demo/skills/demo"
            skill_source.mkdir(parents=True)
            (skill_source / "SKILL.md").write_text("---\nname: demo\ndescription: v1\n---\n", encoding="utf-8")
            (root / "runtime.py").write_text("runtime-v1\n", encoding="utf-8")
            manifest_path = root / "kits/demo/kit.yaml"
            manifest_path.write_text(json.dumps(_demo_manifest("1.0.0")), encoding="utf-8")
            unrelated = target / "unrelated/SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("user-owned\n", encoding="utf-8")

            first = ba_kit.install(root, target, "demo")
            first_digest = installed_tree_sha256(target)
            second = ba_kit.install(root, target, "demo")

            self.assertEqual(first["installed"], second["installed"])
            self.assertEqual(first_digest, installed_tree_sha256(target))
            self.assertEqual((target / "demo/SKILL.md").read_text(encoding="utf-8").splitlines()[1], "name: demo")
            self.assertEqual((target / ".demo/runtime.py").read_text(encoding="utf-8"), "runtime-v1\n")

            (skill_source / "SKILL.md").write_text("---\nname: demo\ndescription: v2\n---\n", encoding="utf-8")
            (root / "runtime.py").write_text("runtime-v2\n", encoding="utf-8")
            manifest_path.write_text(json.dumps(_demo_manifest("2.0.0")), encoding="utf-8")
            ba_kit.install(root, target, "demo")

            self.assertIn("description: v2", (target / "demo/SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual((target / ".demo/runtime.py").read_text(encoding="utf-8"), "runtime-v2\n")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned\n")

            managed_file = target / ".demo/runtime.py"
            managed_file.write_text("local edit\n", encoding="utf-8")
            (root / "runtime.py").write_text("runtime-v3\n", encoding="utf-8")
            manifest_path.write_text(json.dumps(_demo_manifest("3.0.0")), encoding="utf-8")
            result = ba_kit.install(root, target, "demo")
            self.assertIn(".demo/runtime.py", result["preserved"])
            self.assertEqual(managed_file.read_text(encoding="utf-8"), "local edit\n")

            removed = ba_kit.uninstall(target, "demo")
            self.assertIn("demo", removed["removed"])
            self.assertIn(".demo/runtime.py", removed["preserved"])
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned\n")

    def test_upgrade_rollback_preserves_prior_install_when_record_write_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            target = Path(temp) / "project/.agents/skills"
            skill_source = root / "kits/demo/skills/demo"
            skill_source.mkdir(parents=True)
            skill_file = skill_source / "SKILL.md"
            skill_file.write_text("---\nname: demo\ndescription: v1\n---\n", encoding="utf-8")
            runtime_source = root / "runtime.py"
            runtime_source.write_text("runtime-v1\n", encoding="utf-8")
            manifest_path = root / "kits/demo/kit.yaml"
            manifest_path.write_text(json.dumps(_demo_manifest("1.0.0")), encoding="utf-8")
            ba_kit.install(root, target, "demo")

            record_path = target / ".demo-kit-install.json"
            prior_record = record_path.read_bytes()
            skill_file.write_text("---\nname: demo\ndescription: v2\n---\n", encoding="utf-8")
            runtime_source.write_text("runtime-v2\n", encoding="utf-8")
            manifest_path.write_text(json.dumps(_demo_manifest("2.0.0")), encoding="utf-8")

            with mock.patch.object(ba_kit, "_write_json", side_effect=OSError("simulated record failure")):
                with self.assertRaisesRegex(OSError, "simulated record failure"):
                    ba_kit.install(root, target, "demo")

            self.assertEqual((target / "demo/SKILL.md").read_text(encoding="utf-8"), "---\nname: demo\ndescription: v1\n---\n")
            self.assertEqual((target / ".demo/runtime.py").read_text(encoding="utf-8"), "runtime-v1\n")
            self.assertEqual(record_path.read_bytes(), prior_record)
            self.assertFalse(any(target.glob(".demo-kit-stage-*")))

    def test_package_digest_uses_file_bytes_not_metadata_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "one"
            second = Path(temp) / "two"
            for root in (first, second):
                (root / "nested").mkdir(parents=True)
                (root / "nested/café.txt").write_bytes(b"payload\n")
            os.utime(first / "nested/café.txt", (1, 1))
            os.utime(second / "nested/café.txt", (2, 2))

            self.assertEqual(installed_tree_sha256(first), installed_tree_sha256(second))
            (second / "nested/café.txt").write_bytes(b"changed\n")
            self.assertNotEqual(installed_tree_sha256(first), installed_tree_sha256(second))
            inventory = package_inventory(first, source_root=first, manifest={"id": "demo", "files": [], "skill_sources": {}, "skills": {"required": [], "optional": []}, "workflow": {"skill": "none"}, "core": []})
            self.assertEqual(inventory[0]["path"], "nested/café.txt")
            self.assertEqual(inventory[0]["classification"], "UNDECLARED_FILE")
            with self.assertRaisesRegex(ValueError, "symlink"):
                try:
                    (first / "link").symlink_to(first / "nested/café.txt")
                except OSError as error:
                    self.skipTest(f"symlink creation is unavailable: {error}")
                installed_tree_sha256(first)

    def test_package_digest_structurally_rejects_symlink_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "simulated-link").write_bytes(b"link target")
            original_is_symlink = Path.is_symlink

            def simulated_symlink(path):
                return path.name == "simulated-link" or original_is_symlink(path)

            with mock.patch.object(Path, "is_symlink", simulated_symlink):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    installed_tree_sha256(root)

    def test_installed_runtime_imports_from_target_and_keeps_core_free_of_optional_deps(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-installed-") as temp:
            project = Path(temp) / "project"
            target = project / ".agents/skills"
            target.mkdir(parents=True)
            ba_kit.install(ROOT, target, "test")
            runtime = target / ".test-kit"
            script = "\n".join([
                "import os, pathlib, sys",
                "root=pathlib.Path(sys.argv[1]).resolve()",
                "sys.path.insert(0, str(root))",
                "from tooling.lib import test_kit_v1, test_kit_v1_cases, codex_cli",
                "assert pathlib.Path(test_kit_v1.__file__).resolve().is_relative_to(root)",
                "assert pathlib.Path(test_kit_v1_cases.__file__).resolve().is_relative_to(root)",
                "assert not any(pathlib.Path(p or '.').resolve().is_relative_to(pathlib.Path(sys.argv[2]).resolve()) for p in sys.path)",
                "try:",
                "    from tooling.lib import test_kit_v1_excel",
                "except ModuleNotFoundError as error:",
                "    assert error.name == 'openpyxl'",
                "else:",
                "    raise AssertionError('Excel dependencies unexpectedly available under -S')",
                "from tooling.lib import test_kit_v1_xmind as xmind",
                "old_path=os.environ.get('PATH', '')",
                "os.environ['PATH']=''",
                "try:",
                "    xmind._serialize_xmind({}, pathlib.Path.cwd(), 'optional-smoke')",
                "except xmind.XMindProjectionError as error:",
                "    assert error.code == 'XMIND_SDK_UNAVAILABLE'",
                "else:",
                "    raise AssertionError('XMind ran without its explicit dependencies')",
                "finally:",
                "    os.environ['PATH']=old_path",
            ])
            result = subprocess.run(
                [sys.executable, "-S", "-c", script, str(runtime), str(ROOT)],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_clean_installed_native_workflow_uses_installed_skills_and_runtime(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-installed-flow-") as temp:
            project = Path(temp) / "project"
            target = project / ".agents/skills"
            target.mkdir(parents=True)
            ba_kit.install(ROOT, target, "test")
            runtime = target / ".test-kit"
            script_path = Path(temp) / "installed_smoke.py"
            script_path.write_bytes((ROOT / "tooling/tests/fixtures/installed_package_smoke.py").read_bytes())
            codex_stub = project / "codex-stub.exe"
            codex_stub.write_bytes(b"temporary Codex stub")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(runtime)
            env["TEST_KIT_CODEX_COMMAND"] = str(codex_stub)
            result = subprocess.run(
                [sys.executable, "-S", str(script_path), str(runtime), str(ROOT)],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("INSTALLED_SMOKE: PASS", result.stdout)

    def test_inventory_covers_installed_files_with_source_classification(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / ".agents/skills"
            ba_kit.install(ROOT, target, "test")
            manifest = ba_kit.load_manifest(ROOT, "test")
            inventory = package_inventory(target, source_root=ROOT, manifest=manifest)
            paths = {item["path"] for item in inventory}
            self.assertIn("test-kit/SKILL.md", paths)
            self.assertIn("bmad-testarch-test-design/SKILL.md", paths)
            self.assertIn("create-test-cases/SKILL.md", paths)
            self.assertIn(".test-kit/tooling/lib/test_kit_v1.py", paths)
            self.assertIn(".test-kit-install.json", paths)
            self.assertIn(".test-kit/package-authority.json", paths)
            actual_paths = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()}
            self.assertEqual(paths, actual_paths)
            self.assertFalse(any(path.startswith("benchmark/") or "tooling/tests" in path for path in paths))
            self.assertFalse(any(item["classification"] == "UNDECLARED_FILE" for item in inventory))


def _seal_integrity_package(root, manifest):
    manifest_path = root / "kits" / manifest["id"] / "kit.yaml"
    authority_source = root / "kits" / manifest["id"] / "package-authority.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    authority = build_package_authority(root, manifest)
    authority_bytes = package_authority_bytes(authority)
    authority_source.write_bytes(authority_bytes)
    manifest["integrity"]["authority"]["sha256"] = hashlib.sha256(authority_bytes).hexdigest()
    manifest["integrity"]["payload"]["sha256"] = authority["payload_tree_sha256"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _demo_manifest(version):
    return {
        "schema_version": 1,
        "id": "demo",
        "name": "Demo",
        "version": version,
        "workflow": {"skill": "demo"},
        "core": [],
        "skills": {"required": [], "optional": []},
        "skill_sources": {"demo": "kits/demo/skills/demo"},
        "install_metadata": {"source_repository": "demo"},
        "files": [
            {"source": "runtime.py", "destination": ".demo/runtime.py", "classification": "CORE_RUNTIME"}
        ],
    }


if __name__ == "__main__":
    unittest.main()
