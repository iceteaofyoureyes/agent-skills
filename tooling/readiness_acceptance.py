"""Pre-Golden fixture acceptance and evidence. This command never starts a Golden run."""
import argparse
import io
import json
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tooling.sdlc_suite import ROOT, doctor, lock_data
from tooling.tests.test_sdlc_acceptance import FreshSyntheticAcceptance
from tooling import install_dev_kit
from tooling.lib import dev_kit


def acceptance(spec_kit_cli, codex_home):
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(FreshSyntheticAcceptance)
    tests.addTest(FreshSyntheticAcceptance("check_preparation_patches_preserve_authority_and_ignore_runtime"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(tests)
    with tempfile.TemporaryDirectory(prefix="sdlc-installed-dev-doctor-") as temp:
        installed = install_dev_kit.install(ROOT, Path(temp) / "runtime")
        app = Path(temp) / "app"
        app.mkdir()
        installed_dev = dev_kit.doctor(Path(installed["runtime_root"]), project_root=app, codex_home=codex_home,
                                      spec_kit_cli=spec_kit_cli, mode="benchmark")
    suite = doctor(spec_kit_cli=spec_kit_cli, codex_home=codex_home)
    # Evidence indexes identities/results, not ephemeral paths or agent profile data.
    report = {"schema_version": 1, "evidence_class": "SYNTHETIC_FRAMEWORK_ACCEPTANCE_ONLY", "golden_run": "NOT_STARTED",
              "recorded_at": datetime.now(timezone.utc).isoformat(), "toolchain": lock_data(),
              "suite_lock_sha256": hashlib.sha256((ROOT / "tooling/sdlc-suite-lock.json").read_bytes()).hexdigest(),
              "synthetic_tests": {"total": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped)},
              "per_kit_doctors": {kit: value["status"] for kit, value in suite["per_kit"].items()},
              "suite_doctor": {"status": suite["status"], "checks": [{"name": row["name"], "status": row["status"]} for row in suite["checks"]]},
              "installed_dev_doctor": {"status": installed_dev["status"], "context_purity": installed_dev["context_purity"]},
              "status": "READY_FOR_GOLDEN_RUN" if result.wasSuccessful() and not result.skipped and suite["status"] == "READY" and installed_dev["status"] == "READY" else "GOLDEN_READINESS_BLOCKED"}
    return report, stream.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-kit-cli", type=Path, required=True)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, output = acceptance(args.spec_kit_cli, args.codex_home)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "READY_FOR_GOLDEN_RUN" else 1)
