"""Synthetic framework fixtures only. No Golden business evidence or Human approval."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace

from tooling.lib import ba_kit, dev_kit, test_kit_v1 as test, test_kit_v1_cases as cases
from approved_baseline import read_approved_baseline
from delivery_manifest import load_delivery_manifest
from tooling.tests.test_dev_kit import _write_approved_baseline


def delivery_fixture(root, ux=True):
    root = Path(root)
    handoff = _write_approved_baseline(root)
    contract = root / "ux-contract.md"
    contract.write_text("# Synthetic UX semantics\nThe submit control confirms the user's selection.\n", encoding="utf-8")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = root / "ux-approval.json"
    receipt.write_text(json.dumps({"schema_version": 1, "feature_id": "CR-001",
        "source": {"path": contract.name, "revision": "UX-001", "sha256": digest(contract)},
        "approver": {"role": "HUMAN", "identity": "synthetic-human"}, "decision": "APPROVE"}), encoding="utf-8")
    data = {"schema_version": 2, "feature": {"id": "CR-001"}, "delivery_revision": "CR-001-DELIVERY-001",
            "ba": {"handoff": {"path": handoff.name, "revision": "ba-rev-test", "sha256": digest(handoff)}},
            "ux": {"required": ux}, "targets": [{"repository": "fixture/app", "module": "app", "base_revision": "a" * 40}],
            "open_items": {"blocking": []}}
    if ux:
        data["ux"]["contract"] = {"path": contract.name, "revision": "UX-001", "sha256": digest(contract)}
        data["ux"]["approval_receipt"] = {"path": receipt.name, "sha256": digest(receipt)}
    path = root / "delivery-manifest.yml"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


class SharedBaselineTests(unittest.TestCase):
    def test_skill_payload_excludes_generated_bytecode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            skill = root / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Fixture\n---\n", encoding="utf-8")
            original = ba_kit.tree_hash(skill)
            (skill / "__pycache__").mkdir()
            (skill / "__pycache__/generated.pyc").write_bytes(b"ephemeral cache")
            self.assertEqual(ba_kit.tree_hash(skill), original)
            manifest = root / "kits/fixture/kit.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"schema_version": 1, "id": "fixture", "name": "Fixture", "version": "1.0.0",
                "workflow": {"skill": "demo"}, "core": [], "skills": {"required": [], "optional": []}, "outputs": []}), encoding="utf-8")
            target = Path(temp) / "installed"
            ba_kit.install(root, target, "fixture")
            self.assertFalse(list(target.rglob("*.pyc")))
            self.assertEqual(ba_kit.doctor(root, target, "fixture")["status"], "READY")

    def test_no_business_ids_deterministic_and_same_dev_test_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            handoff = _write_approved_baseline(temp)
            ba = read_approved_baseline(handoff)
            self.assertEqual(ba, test.load_approved_baseline(handoff))
            self.assertEqual(ba.identity, dev_kit.snapshot_approved_baseline(handoff)["identity"])
            self.assertEqual(ba, read_approved_baseline(handoff))
            self.assertEqual(ba.ba_ids, {"BAREF:SRS:001", "BAREF:BR:001"})
            for row in (*ba.requirements, *ba.business_rules):
                self.assertEqual(len(row.locator_sha256), 64)
                self.assertTrue(row.source_sha256)
                self.assertGreater(row.ordinal, 0)
            refs = test._parse_ref_cell("BAREF:SRS:001; BAREF:BR:001", ba.ba_ids, path="fixture", line=1, field="trace")
            self.assertEqual(set(refs), ba.ba_ids)
            self.assertEqual(cases._parse_explicit_refs("BAREF:SRS:001; TD-001", case_id="TC-001", field="trace"), ["BAREF:SRS:001", "TD-001"])

    def test_real_domain_ids_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "rules.md"
            p.write_text("## BR-WED-011 — Access\nOnly the owner can edit.\n", encoding="utf-8")
            self.assertEqual(test._parse_source_rows(p, "BR", 3)[0].id, "BR-WED-011")
            p.write_text("| ID | Text | Status |\n|---|---|---|\n| FR-001 | Save | CONFIRMED |\n", encoding="utf-8")
            self.assertEqual(test._parse_source_rows(p, "FR", 3)[0].id, "FR-001")
            p.write_text("- BR-AUTH-004: Only the owner can edit.\n", encoding="utf-8")
            self.assertEqual(test._parse_source_rows(p, "BR", 3)[0].id, "BR-AUTH-004")
            p.write_text("| ID | Rule |\n|---|---|\n| BR-WED-011 | Access |\n", encoding="utf-8")
            self.assertEqual(test._parse_source_rows(p, "BR", 3)[0].id, "BR-WED-011")

    def test_locator_binding_is_portable_across_same_declared_bytes(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = read_approved_baseline(_write_approved_baseline(first))
            b = read_approved_baseline(_write_approved_baseline(second))
            self.assertEqual([(row.id, row.locator_sha256) for row in a.requirements], [(row.id, row.locator_sha256) for row in b.requirements])

    def test_hash_mismatch_and_post_start_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            handoff = _write_approved_baseline(temp)
            snapshot = dev_kit.snapshot_approved_baseline(handoff)
            (Path(temp) / "srs.md").write_text("Changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_approved_baseline(handoff)
            self.assertTrue(dev_kit.verify_baseline(snapshot))


class DeliveryTests(unittest.TestCase):
    def test_GR_DWC_DEMO_001_20261002_01_immutable_semantics_external_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            source = Path(temp) / data["ux"]["contract"]["path"]
            approved_bytes = source.read_bytes()
            self.assertNotIn(b"revision:", approved_bytes)
            self.assertNotIn(b"status: APPROVED", approved_bytes)
            load_delivery_manifest(path)
            self.assertEqual(source.read_bytes(), approved_bytes)

    def test_external_receipt_binding_rejects_invalid_authority(self):
        mutations = ("source_hash", "receipt_source_hash", "receipt_revision", "receipt_decision",
                     "missing_receipt", "missing_receipt_file", "tampered_receipt", "receipt_hash",
                     "receipt_feature", "receipt_role", "receipt_identity", "receipt_path", "v1")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                path, data = delivery_fixture(temp)
                receipt_path = Path(temp) / data["ux"]["approval_receipt"]["path"]
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if mutation == "source_hash": data["ux"]["contract"]["sha256"] = "0" * 64
                if mutation == "receipt_source_hash": receipt["source"]["sha256"] = "0" * 64
                if mutation == "receipt_revision": receipt["source"]["revision"] = "UX-002"
                if mutation == "receipt_decision": receipt["decision"] = "REJECT"
                if mutation == "receipt_feature": receipt["feature_id"] = "CR-002"
                if mutation == "receipt_role": receipt["approver"]["role"] = "AI"
                if mutation == "receipt_identity": receipt["approver"]["identity"] = ""
                if mutation == "receipt_path": receipt["source"]["path"] = "other.md"
                if mutation.startswith("receipt_") and mutation != "receipt_hash":
                    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                    data["ux"]["approval_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
                if mutation == "missing_receipt": del data["ux"]["approval_receipt"]
                if mutation == "missing_receipt_file": receipt_path.unlink()
                if mutation == "tampered_receipt": receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
                if mutation == "receipt_hash": data["ux"]["approval_receipt"]["sha256"] = "0" * 64
                if mutation == "v1": data["schema_version"] = 1
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_delivery_manifest(path)

    def test_prototype_cannot_replace_approved_semantic_source(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            prototype = Path(temp) / "prototype.html"
            prototype.write_text("<button>Confirm</button>", encoding="utf-8")
            data["ux"]["contract"] = {"path": prototype.name, "revision": "UX-001",
                "sha256": hashlib.sha256(prototype.read_bytes()).hexdigest()}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_delivery_manifest(path)

    def test_prototype_is_only_review_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            prototype = Path(temp) / "prototype.html"
            prototype.write_text("<button>Confirm</button>", encoding="utf-8")
            data["ux"]["prototype"] = {"path": prototype.name,
                "sha256": hashlib.sha256(prototype.read_bytes()).hexdigest(), "authority": "REVIEW_EVIDENCE"}
            path.write_text(json.dumps(data), encoding="utf-8")
            load_delivery_manifest(path)
            original = dict(data["ux"]["prototype"])
            data["ux"]["prototype"].update({key: data["ux"]["contract"][key] for key in ("path", "sha256")})
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prototype cannot also"):
                load_delivery_manifest(path)
            data["ux"]["prototype"] = original
            for authority in ("SEMANTIC_AUTHORITY", "APPROVED", ""):
                with self.subTest(authority=authority):
                    data["ux"]["prototype"]["authority"] = authority
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_delivery_manifest(path)

    def test_required_ux_and_optional_no_ux(self):
        with tempfile.TemporaryDirectory() as temp:
            for required in (True, False):
                path, _ = delivery_fixture(temp, required)
                self.assertEqual(load_delivery_manifest(path)["baseline"].feature_id, "CR-001")

    def test_missing_ux_hash_revision_and_blocking_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            for mutation in ("missing", "hash", "revision", "blocking", "base", "unsafe", "credential"):
                candidate = json.loads(json.dumps(data))
                if mutation == "missing": del candidate["ux"]["contract"]
                if mutation == "hash": candidate["ba"]["handoff"]["sha256"] = "0" * 64
                if mutation == "revision": candidate["ux"]["contract"]["revision"] = "UX-002"
                if mutation == "blocking": candidate["open_items"]["blocking"] = ["OPEN"]
                if mutation == "base": candidate["targets"][0]["base_revision"] = "main"
                if mutation == "unsafe": candidate["ux"]["contract"]["path"] = "../outside.md"
                if mutation == "credential": candidate["ba"]["credentials"] = "forbidden synthetic field"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    load_delivery_manifest(path)

    def test_yaml_target_sequence(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp, False)
            ref = data["ba"]["handoff"]
            path.write_text(f"schema_version: 2\nfeature:\n  id: CR-001\ndelivery_revision: CR-001-DELIVERY-001\nba:\n  handoff:\n    path: {ref['path']}\n    revision: {ref['revision']}\n    sha256: {ref['sha256']}\nux:\n  required: false\ntargets:\n  - repository: fixture/app\n    module: app\n    base_revision: {'a'*40}\nopen_items:\n  blocking: []\n", encoding="utf-8")
            self.assertEqual(load_delivery_manifest(path)["data"], data)


class DependencyTests(unittest.TestCase):
    def test_each_type_and_gate_separation(self):
        for kind in sorted(cases.DEPENDENCY_TYPES):
            with self.subTest(kind=kind):
                dep = cases._dependencies_for_case(f"OPEN execution dependencies: [{kind}] synthetic need", ())[0]
                self.assertEqual(dep.kind, kind)
                row = cases.CanonicalTestcase("TC-001", "Synthetic", "Synthetic", "Ready", None, (), "P1", ("BAREF:SRS:001",), ("TD-001",), (dep,))
                snapshot = cases.CaseSnapshot.create((row,), artifact_id="CASES", revision="1")
                self.assertEqual(cases.has_open_semantic_dependencies(snapshot), kind == "SEMANTIC_ORACLE")
                for status in ("RESOLVED", "NOT_REQUIRED"):
                    changed = replace(row, execution_dependencies=(replace(dep, status=status),))
                    resolved = cases.CaseSnapshot.create((changed,), artifact_id="CASES", revision="2")
                    self.assertFalse(cases.has_open_semantic_dependencies(resolved))
