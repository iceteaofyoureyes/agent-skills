"""Synthetic framework fixtures only. No Golden business evidence or Human approval."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace

from tooling.lib import dev_kit, test_kit_v1 as test, test_kit_v1_cases as cases
from approved_baseline import read_approved_baseline
from delivery_manifest import load_delivery_manifest
from tooling.tests.test_dev_kit import _write_approved_baseline


def delivery_fixture(root, ux=True):
    root = Path(root)
    handoff = _write_approved_baseline(root)
    contract = root / "ux-contract.md"
    contract.write_text("revision: UX-001\nstatus: APPROVED\nSynthetic interaction authority.\n", encoding="utf-8")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    data = {"schema_version": 1, "feature": {"id": "CR-001"}, "delivery_revision": "CR-001-DELIVERY-001",
            "ba": {"handoff": {"path": handoff.name, "revision": "ba-rev-test", "sha256": digest(handoff)}},
            "ux": {"required": ux}, "targets": [{"repository": "fixture/app", "module": "app", "base_revision": "a" * 40}],
            "open_items": {"blocking": []}}
    if ux:
        data["ux"]["contract"] = {"path": contract.name, "revision": "UX-001", "sha256": digest(contract)}
    path = root / "delivery-manifest.yml"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


class SharedBaselineTests(unittest.TestCase):
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

    def test_hash_mismatch_and_post_start_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            handoff = _write_approved_baseline(temp)
            snapshot = dev_kit.snapshot_approved_baseline(handoff)
            (Path(temp) / "srs.md").write_text("Changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_approved_baseline(handoff)
            self.assertTrue(dev_kit.verify_baseline(snapshot))


class DeliveryTests(unittest.TestCase):
    def test_required_ux_and_optional_no_ux(self):
        with tempfile.TemporaryDirectory() as temp:
            for required in (True, False):
                path, _ = delivery_fixture(temp, required)
                self.assertEqual(load_delivery_manifest(path)["baseline"].feature_id, "CR-001")

    def test_missing_ux_hash_revision_and_blocking_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            for mutation in ("missing", "hash", "revision", "blocking", "base", "unsafe"):
                candidate = json.loads(json.dumps(data))
                if mutation == "missing": del candidate["ux"]["contract"]
                if mutation == "hash": candidate["ba"]["handoff"]["sha256"] = "0" * 64
                if mutation == "revision": candidate["ux"]["contract"]["revision"] = "UX-002"
                if mutation == "blocking": candidate["open_items"]["blocking"] = ["OPEN"]
                if mutation == "base": candidate["targets"][0]["base_revision"] = "main"
                if mutation == "unsafe": candidate["ux"]["contract"]["path"] = "../outside.md"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    load_delivery_manifest(path)

    def test_yaml_target_sequence(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp, False)
            ref = data["ba"]["handoff"]
            path.write_text(f"schema_version: 1\nfeature:\n  id: CR-001\ndelivery_revision: CR-001-DELIVERY-001\nba:\n  handoff:\n    path: {ref['path']}\n    revision: {ref['revision']}\n    sha256: {ref['sha256']}\nux:\n  required: false\ntargets:\n  - repository: fixture/app\n    module: app\n    base_revision: {'a'*40}\nopen_items:\n  blocking: []\n", encoding="utf-8")
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
