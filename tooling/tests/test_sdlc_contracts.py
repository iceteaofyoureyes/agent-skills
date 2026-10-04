"""Synthetic framework fixtures only. No Golden business evidence or Human approval."""
import hashlib
import json
import tempfile
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from dataclasses import replace

from tooling.lib import ba_kit, dev_kit, test_kit_v1 as test, test_kit_v1_cases as cases
from approved_baseline import BaselineError, _parse_source_rows, read_approved_baseline
from delivery_manifest import load_delivery_manifest
from tooling.tests.test_dev_kit import _write_approved_baseline
from tooling.install_dev_kit import install as install_dev


def delivery_fixture(root, ux=True):
    root = Path(root)
    handoff = _write_approved_baseline(root)
    fixture = Path(__file__).parent / 'fixtures/delivery-ux-canonical/ux'
    shutil.copytree(fixture, root / 'ux', dirs_exist_ok=True)
    contract = root / 'ux/ux-contract.md'
    receipt = root / 'ux/approval-receipt.json'
    prototype = root / 'ux/prototype.html'
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    data = {"schema_version": 2, "feature": {"id": "CR-001"}, "delivery_revision": "CR-001-DELIVERY-001",
            "ba": {"handoff": {"path": handoff.name, "revision": "ba-rev-test", "sha256": digest(handoff)}},
            "ux": {"required": ux}, "targets": [{"repository": "fixture/app", "module": "app", "base_revision": "a" * 40}],
            "open_items": {"blocking": []}}
    if ux:
        data["ux"]["contract"] = {"path": "ux/ux-contract.md", "revision": "UX-001", "sha256": digest(contract)}
        data["ux"]["approval_receipt"] = {"path": "ux/approval-receipt.json", "sha256": digest(receipt)}
        data["ux"]["prototype"] = {"path": "ux/prototype.html", "sha256": digest(prototype), "authority": "REVIEW_EVIDENCE"}
    path = root / "delivery-manifest.yml"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


def generalized_delivery_fixture(root, prototype=True):
    path, data = delivery_fixture(root)
    receipt_path = Path(root) / data["ux"]["approval_receipt"]["path"]
    receipt = json.loads(receipt_path.read_text())
    receipt["schema_version"] = 2
    receipt["semantic_snapshot_sha256_method"] = "UX_APPROVED_SOURCES_CANONICAL_JSON_SHA256_V2"
    if not prototype:
        data["ux"].pop("prototype")
        receipt["sources"].pop("ux/prototype.html")
        receipt.pop("prototype_authority")
        (Path(root) / "ux/prototype.html").unlink()
    receipt["semantic_snapshot_sha256"] = hashlib.sha256(json.dumps(receipt["sources"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    data["ux"]["approval_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data


class SharedBaselineTests(unittest.TestCase):
    def test_inline_code_source_ids_normalize_across_source_extraction_paths(self):
        fixtures = (
            ("table", "BR", "| `BR-DASH-001` | Rule text. | Confirmed |\n", "BR-DASH-001"),
            ("heading", "FR", "## `FR-ABC-001` — Heading title\nRequirement text.\n", "FR-ABC-001"),
            ("legacy", "BR", "- `BR-ABC-002`: Rule text.\n", "BR-ABC-002"),
        )
        with tempfile.TemporaryDirectory() as temp:
            for name, prefix, source, expected in fixtures:
                path = Path(temp) / f"{name}.md"
                path.write_text(source, encoding="utf-8")
                with self.subTest(name=name):
                    self.assertEqual([row.id for row in _parse_source_rows(path, prefix, 3)], [expected])

    def test_cr_dwc_inline_id_fixture_exposes_all_canonical_business_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            handoff = _write_approved_baseline(root)
            rules = Path(root) / "rules.md"
            fixture = Path(__file__).parent / "fixtures/approved-baseline-inline-ids/business-rules.md"
            rules.write_bytes(fixture.read_bytes())
            original_source = rules.read_bytes()
            text = handoff.read_text(encoding="utf-8")
            fields, _, _, _ = dev_kit._yaml_fields(text)
            digest = hashlib.sha256(original_source).hexdigest()
            old_digest = fields[("authoritative_sources", "business_rules", "sha256")]
            handoff.write_text(text.replace(old_digest, digest), encoding="utf-8")

            baseline = read_approved_baseline(handoff)
            expected = {f"BR-DASH-{number:03d}" for number in range(1, 7)}
            self.assertEqual(baseline.business_rule_ids, expected)
            self.assertFalse(any(identifier.startswith("BAREF:BR:") for identifier in baseline.business_rule_ids))
            self.assertEqual(rules.read_bytes(), original_source)

    def test_malformed_inline_ids_and_arbitrary_text_are_not_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rules.md"
            path.write_text(
                "| ID | Rule | Note |\n|---|---|---|\n"
                "| ``BR-001`` | Double wrapper. | Confirmed |\n"
                "| `BR-002 | Missing close. | Confirmed |\n"
                "| BR-003` | Missing open. | Confirmed |\n"
                "| NOT-A-BR | Arbitrary text. | Confirmed |\n",
                encoding="utf-8",
            )
            rows = _parse_source_rows(path, "BR", 3)
            self.assertTrue(all(row.id.startswith("BAREF:BR:") for row in rows))
            self.assertFalse(any(row.id in {"BR-001", "BR-002", "BR-003", "NOT-A-BR"} for row in rows))

    def test_duplicate_id_after_inline_code_normalization_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rules.md"
            path.write_text(
                "| ID | Rule | Note |\n|---|---|---|\n"
                "| BR-001 | Plain ID. | Confirmed |\n"
                "| `BR-001` | Same canonical ID. | Confirmed |\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BaselineError, "duplicate BR source IDs"):
                _parse_source_rows(path, "BR", 3)

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
    def test_generalized_approval_with_and_without_optional_prototype(self):
        for prototype in (False, True):
            with self.subTest(prototype=prototype), tempfile.TemporaryDirectory() as temp:
                path, _ = generalized_delivery_fixture(temp, prototype)
                load_delivery_manifest(path)

    def test_generalized_version_method_and_unapproved_prototype_rejected(self):
        for mutation in ("legacy_method", "unknown_version", "unapproved_prototype", "prototype_authority"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                path, data = generalized_delivery_fixture(temp, False)
                receipt_path = Path(temp) / data["ux"]["approval_receipt"]["path"]
                receipt = json.loads(receipt_path.read_text())
                if mutation == "legacy_method":
                    receipt["semantic_snapshot_sha256_method"] = json.loads((Path(__file__).parent / "fixtures/delivery-ux-canonical/ux/approval-receipt.json").read_text())["semantic_snapshot_sha256_method"]
                if mutation == "unknown_version": receipt["schema_version"] = 3
                if mutation == "prototype_authority": receipt["prototype_authority"] = "SEMANTIC_AUTHORITY"
                if mutation == "unapproved_prototype":
                    prototype = Path(temp) / "ux/prototype.html"
                    prototype.write_text("Unapproved", encoding="utf-8")
                    data["ux"]["prototype"] = {"path": "ux/prototype.html", "sha256": hashlib.sha256(prototype.read_bytes()).hexdigest(), "authority": "REVIEW_EVIDENCE"}
                receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                data["ux"]["approval_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_delivery_manifest(path)

    def test_declared_optional_prototype_missing_or_tampered_fails_closed(self):
        for version in (1, 2):
            for manifest_prototype in (False, True):
                for missing in (False, True):
                    with self.subTest(version=version, manifest=manifest_prototype, missing=missing), tempfile.TemporaryDirectory() as temp:
                        path, data = delivery_fixture(temp)
                        receipt_path = Path(temp) / data["ux"]["approval_receipt"]["path"]
                        receipt = json.loads(receipt_path.read_text())
                        if version == 2:
                            receipt["schema_version"] = 2
                            receipt["semantic_snapshot_sha256_method"] = "UX_APPROVED_SOURCES_CANONICAL_JSON_SHA256_V2"
                        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                        data["ux"]["approval_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
                        if not manifest_prototype:
                            data["ux"].pop("prototype")
                        path.write_text(json.dumps(data), encoding="utf-8")
                        prototype = Path(temp) / "ux/prototype.html"
                        if missing:
                            prototype.unlink()
                        else:
                            prototype.write_text("Tampered", encoding="utf-8")
                        with self.assertRaises(ValueError):
                            load_delivery_manifest(path)

    def test_distributed_ba_dev_test_validate_canonical_receipt(self):
        source = Path(__file__).resolve().parents[2]
        versions = {"ba": "2.0.0-rc.3", "dev": "0.4.0-rc.1", "test": "2.0.0-rc.7"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            feature = root / "feature"
            feature.mkdir()
            manifest, data = delivery_fixture(feature)
            digest = hashlib.sha256((source / "ba-workflow/scripts/delivery_manifest.py").read_bytes()).hexdigest()
            for kit, version in versions.items():
                with self.subTest(kit=kit):
                    self.assertEqual(json.loads((source / f"kits/{kit}/kit.yaml").read_text())["version"], version)
                    target = root / kit
                    if kit == "dev":
                        installed = install_dev(source, target)
                        record = json.loads(Path(installed["manifest"]).read_text())
                        self.assertEqual(record["kit_version"], version)
                        scripts = Path(installed["runtime_root"]) / "ba-workflow/scripts"
                    else:
                        ba_kit.install(source, target, kit)
                        scripts = target / ("ba-workflow/scripts" if kit == "ba" else ".test-kit/ba-workflow/scripts")
                    self.assertEqual(hashlib.sha256((scripts / "delivery_manifest.py").read_bytes()).hexdigest(), digest)
                    code = "import sys; sys.path.insert(0,sys.argv[1]); from delivery_manifest import load_delivery_manifest; load_delivery_manifest(sys.argv[2])"
                    run = lambda: subprocess.run([sys.executable, "-I", "-c", code, str(scripts), str(manifest)], capture_output=True, text=True)
                    manifest.write_text(json.dumps(data), encoding="utf-8")
                    result = run()
                    self.assertEqual(result.returncode, 0, result.stderr)
                    changed = json.loads(json.dumps(data))
                    changed["ux"]["approval_receipt"]["sha256"] = "0" * 64
                    manifest.write_text(json.dumps(changed), encoding="utf-8")
                    result = run()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("SHA-256 mismatch", result.stderr)
                    for prototype in (False, True):
                        generalized_delivery_fixture(feature, prototype)
                        result = run()
                        self.assertEqual(result.returncode, 0, result.stderr)
                    delivery_fixture(feature)

    def test_GR_DWC_DEMO_001_20261002_01_immutable_semantics_external_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            source = Path(temp) / data["ux"]["contract"]["path"]
            approved_bytes = source.read_bytes()
            self.assertNotIn(b"revision:", approved_bytes)
            self.assertNotIn(b"status: APPROVED", approved_bytes)
            load_delivery_manifest(path)
            self.assertEqual(source.read_bytes(), approved_bytes)

    def test_aggregate_is_recomputed_from_sorted_sources_even_without_manifest_prototype(self):
        with tempfile.TemporaryDirectory() as temp:
            path, data = delivery_fixture(temp)
            receipt_path = Path(temp) / data["ux"]["approval_receipt"]["path"]
            receipt = json.loads(receipt_path.read_text())
            receipt["sources"] = dict(reversed(list(receipt["sources"].items())))
            data["ux"].pop("prototype")
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            data["ux"]["approval_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            path.write_text(json.dumps(data), encoding="utf-8")
            load_delivery_manifest(path)
            prototype = Path(temp) / "ux/prototype.html"
            prototype.write_text("Changed review evidence", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                load_delivery_manifest(path)
            # Rebinding individual hashes cannot bypass the originally approved aggregate.
            receipt["sources"]["ux/prototype.html"] = hashlib.sha256(prototype.read_bytes()).hexdigest()
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            data["ux"]["approval_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "semantic snapshot SHA-256 mismatch"):
                load_delivery_manifest(path)

    def test_external_receipt_binding_rejects_invalid_authority(self):
        mutations = ("source_hash", "receipt_source_hash", "receipt_revision", "receipt_decision",
                     "missing_receipt", "missing_receipt_file", "tampered_receipt", "receipt_hash",
                     "receipt_feature", "receipt_role", "receipt_identity", "receipt_path", "v1",
                     "receipt_snapshot", "receipt_method", "receipt_immutable", "receipt_reapproval",
                     "receipt_prototype_hash", "receipt_prototype_authority", "receipt_commit",
                     "receipt_branch", "receipt_timestamp", "receipt_missing_source", "receipt_extra_source",
                     "prototype_hash", "prototype_bytes", "source_bytes", "receipt_alias_path")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                path, data = delivery_fixture(temp)
                receipt_path = Path(temp) / data["ux"]["approval_receipt"]["path"]
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if mutation == "source_hash": data["ux"]["contract"]["sha256"] = "0" * 64
                if mutation == "receipt_source_hash": receipt["sources"]["ux/ux-contract.md"] = "0" * 64
                if mutation == "receipt_revision": receipt["revision"] = "UX-002"
                if mutation == "receipt_decision": receipt["decision"] = "REJECT"
                if mutation == "receipt_feature": receipt["feature_id"] = "CR-002"
                if mutation == "receipt_role": receipt["approved_by"] = "AI"
                if mutation == "receipt_identity": receipt["decision_type"] = ""
                if mutation == "receipt_path": receipt["sources"]["other.md"] = receipt["sources"].pop("ux/ux-contract.md")
                if mutation == "receipt_snapshot": receipt["semantic_snapshot_sha256"] = "0" * 64
                if mutation == "receipt_method": receipt["semantic_snapshot_sha256_method"] = "trust-me"
                if mutation == "receipt_immutable": receipt["immutable"] = False
                if mutation == "receipt_reapproval": receipt["reapproval_required_if_source_bytes_change"] = False
                if mutation == "receipt_prototype_hash": receipt["sources"]["ux/prototype.html"] = "0" * 64
                if mutation == "receipt_prototype_authority": receipt["prototype_authority"] = "SEMANTIC_AUTHORITY"
                if mutation == "receipt_commit": receipt["source_commit"] = "main"
                if mutation == "receipt_branch": receipt["source_branch"] = ""
                if mutation == "receipt_timestamp": receipt["recorded_at_utc"] = "2026-99-02T17:04:17Z"
                if mutation == "receipt_missing_source": receipt["sources"].pop("ux/prototype.html")
                if mutation == "receipt_extra_source": receipt["sources"]["extra.md"] = "0" * 64
                if mutation == "receipt_alias_path": receipt["sources"]["ux/./prototype.html"] = receipt["sources"].pop("ux/prototype.html")
                if mutation == "prototype_hash": data["ux"]["prototype"]["sha256"] = "0" * 64
                if mutation == "prototype_bytes": (Path(temp) / "ux/prototype.html").write_text("Changed", encoding="utf-8")
                if mutation == "source_bytes": (Path(temp) / "ux/ux-contract.md").write_text("Changed", encoding="utf-8")
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


class DevApprovalPrecedencePromptTests(unittest.TestCase):
    def test_all_readiness_entrypoints_use_validated_approval_precedence(self):
        root = Path(__file__).resolve().parents[2]
        paths = (
            root / "dev-kit/SKILL.md",
            root / "requirements-gap-auditor/SKILL.md",
            root / "kits/dev/plugin/workflows/dev-normal.workflow.yml",
            root / "kits/dev/plugin/workflows/dev-high-risk.workflow.yml",
        )
        required = (
            "APPROVAL STATE != INLINE LIFECYCLE TEXT",
            "APPROVED_FOR_ENGINEERING",
            "PENDING_HUMAN_REVIEW",
            "open_items.blocking",
            "open_items.non_blocking",
            "SUPERSEDED_BY_DELIVERY_MANIFEST",
            "semantic contradiction",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(root)):
                for phrase in required:
                    self.assertIn(phrase, text)


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
