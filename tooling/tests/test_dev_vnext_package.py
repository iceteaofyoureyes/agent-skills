"""VNext package surfaces stay derived from the executable contracts."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tooling import install_dev_kit
from tooling.lib import dev_vnext as contract
from tooling.lib.dev_vnext_doctor import _contract_errors


ROOT = Path(__file__).resolve().parents[2]


class DevVNextPackageTests(unittest.TestCase):
    def test_v2_schemas_match_contracts_and_key_invariants(self):
        self.assertEqual(_contract_errors(ROOT), [])
        schemas = ROOT / "kits/dev/schemas"
        start = json.loads((schemas / "start-request-v2.schema.json").read_text(encoding="utf-8"))
        impact = json.loads((schemas / "engineering-impact-v2.schema.json").read_text(encoding="utf-8"))
        decision = json.loads((schemas / "engineering-decision-v2.schema.json").read_text(encoding="utf-8"))
        state = json.loads((schemas / "dev-state-v2.schema.json").read_text(encoding="utf-8"))
        approval = json.loads((schemas / "technical-approval-v2.schema.json").read_text(encoding="utf-8"))
        handoff = json.loads((schemas / "dev-handoff-v2.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(start["properties"]["authority_mode"]["enum"], list(contract.MODES))
        check = start["properties"]["checks"]["items"]["properties"]
        self.assertEqual(set(check), {"name", "repository_id", "category", "command"})
        self.assertEqual(impact["properties"]["risk"]["properties"]["level"]["enum"], list(contract.RISK_ORDER))
        self.assertEqual(decision["properties"]["id"]["pattern"], contract.ED_ID["pattern"])
        self.assertEqual(state["properties"]["lifecycle"]["enum"], list(contract.LIFECYCLE))
        self.assertEqual(approval["properties"]["actor_role"]["enum"], ["HUMAN", "TECH_LEAD"])
        self.assertEqual(approval["properties"]["artifact_type"]["enum"], ["DEV_TECHNICAL_APPROVAL"])
        self.assertEqual(handoff["properties"]["artifact_class"]["enum"], ["HANDOFF_MANIFEST"])
        self.assertEqual(handoff["properties"]["state"]["enum"], ["READY_FOR_TEST"])
        coverage_id = handoff["properties"]["requirements_coverage"]["items"]["properties"]["id"]
        self.assertEqual(coverage_id["pattern"], contract.BUSINESS_ID["pattern"])
        self.assertNotIn("BAREF", coverage_id["pattern"])

    def test_installer_fails_closed_on_reparse_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            unsafe = home / "runtime" / "v2"
            with patch.object(install_dev_kit, "_reparse_or_symlink", side_effect=lambda path: Path(path) == unsafe):
                with self.assertRaisesRegex(ValueError, "unsafe symlink/reparse path"):
                    install_dev_kit.install(ROOT, home)
            self.assertFalse((home / "runtime/v2").exists())
            self.assertEqual([path for path in home.rglob("*") if path.is_file()], [])

    def test_installer_fails_closed_on_reparse_launcher(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            launcher = home / "bin" / ("devkit.ps1" if os.name == "nt" else "devkit")
            with patch.object(install_dev_kit, "_reparse_or_symlink", side_effect=lambda path: Path(path) == launcher):
                with self.assertRaisesRegex(ValueError, "unsafe existing launcher path"):
                    install_dev_kit.install(ROOT, home)
            self.assertFalse((home / "runtime/v2").exists())

    def test_failed_copy_keeps_existing_v2_and_unrelated_user_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            runtime = home / "runtime/v2"
            runtime.mkdir(parents=True)
            sentinel = runtime / "preserved-v2.txt"
            sentinel.write_text("old runtime remains intact\n", encoding="utf-8")
            unrelated = home / "unrelated.txt"
            unrelated.write_text("preserve\n", encoding="utf-8")
            original_copy = shutil.copyfile
            calls = []

            def fail_after_one(source, destination, *args, **kwargs):
                calls.append(source)
                if len(calls) == 2:
                    raise OSError("synthetic partial-copy failure")
                return original_copy(source, destination, *args, **kwargs)

            with patch.object(install_dev_kit.shutil, "copyfile", side_effect=fail_after_one):
                with self.assertRaisesRegex(OSError, "synthetic partial-copy failure"):
                    install_dev_kit.install(ROOT, home)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "old runtime remains intact\n")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "preserve\n")
            self.assertEqual(list((home / "runtime").glob(".v2-stage-*")), [])


if __name__ == "__main__":
    unittest.main()
