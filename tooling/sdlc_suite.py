"""Suite compatibility lock and Doctor; per-kit Doctors remain authoritative."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from tooling.lib import ba_kit, dev_kit
from tooling.lib.package import validate_source_package_integrity

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = {"ba_handoff": 1, "delivery_manifest": 2, "testware_gate": 2, "golden_provenance": 1}


def lock_data(root=ROOT):
    root = Path(root)
    git = lambda *args: subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    return {"schema_version": 1, "suite_id": "agent-assisted-sdlc-v1", "agent_skills_commit": git("rev-parse", "HEAD"),
            "source_tree": git("rev-parse", "HEAD^{tree}"),
            "components": {kit: {"version": json.loads((root / "kits" / kit / "kit.yaml").read_text(encoding="utf-8"))["version"]}
                           for kit in ("ba", "dev", "test")}, "contracts": CONTRACTS}


def generate_lock(root=ROOT):
    root = Path(root)
    if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip():
        raise ValueError("suite lock requires a clean committed source tree")
    data = lock_data(root)
    (root / "tooling/sdlc-suite-lock.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return data


def check_runtime_ignores(project, lane):
    paths = [".test-kit/runs/SYNTHETIC/runtime.json", ".test-kit/runtime/output.md", "test-runs/legacy/log.json"] if lane == "docs" else [".devkit/runs/SYNTHETIC/input.json", ".specify/workflows/runs/SYNTHETIC/state.json"]
    for path in paths:
        result = subprocess.run(["git", "-C", str(project), "check-ignore", "--quiet", path], capture_output=True)
        if result.returncode != 0:
            raise ValueError(f"runtime path is not ignored: {path}")
    if lane == "app" and subprocess.run(["git", "-C", str(project), "check-ignore", "--quiet", ".specify/project-config.yml"], capture_output=True).returncode == 0:
        raise ValueError("versioned Spec Kit config must remain visible")
    return "PASS"


def doctor(root=ROOT, *, spec_kit_cli, codex_home, docs_project=None, app_project=None, require_lock=True):
    root = Path(root)
    checks = []
    def check(name, action):
        try:
            value = action()
            checks.append({"name": name, "status": "PASS", "detail": value})
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            checks.append({"name": name, "status": "FAIL", "detail": str(error)})
    def lock_check():
        if json.loads((root / "tooling/sdlc-suite-lock.json").read_text()) != lock_data(root):
            raise ValueError("suite lock does not match current HEAD/version/contracts/tree")
        if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip():
            raise ValueError("suite source is dirty")
        return "MATCH"
    if require_lock:
        check("suite lock", lock_check)
    def profile_check():
        profile = Path(codex_home)
        record = json.loads((profile / "profile-lock.json").read_text(encoding="utf-8"))
        if record.get("agent_skills_commit") != lock_data(root)["agent_skills_commit"] or record.get("native_plugin_registration") != "INSTALLED":
            raise ValueError("agent profile is not pinned/installed from this integration commit")
        for relative, expected in record["files"].items():
            path = profile / relative
            if not path.resolve().is_relative_to(profile.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("pinned agent profile drift: " + relative)
        return "PINNED"
    check("dedicated profile provenance", profile_check)
    check("Test package authority", lambda: validate_source_package_integrity(root, ba_kit.load_manifest(root, "test"))[2])
    def routers():
        for path in (root / "ba-workflow/SKILL.md", root / "dev-kit/SKILL.md", root / "kits/test/skills/test-kit/SKILL.md"):
            if not path.is_file(): raise ValueError("router missing")
        manifests = [ba_kit.load_manifest(root, kit) for kit in ("ba", "test")]
        seen = {}
        for manifest in manifests:
            for name in ba_kit.skill_composition(manifest):
                path = root / manifest.get("skill_sources", {}).get(name, name)
                digest = ba_kit.tree_hash(path)
                if name in seen and seen[name] != digest: raise ValueError("conflicting duplicate skill " + name)
                seen[name] = digest
        from approved_baseline import CONTRACT_VERSION as ba_version
        from delivery_manifest import CONTRACT_VERSION as delivery_version
        from tooling.lib.test_kit_v1_cases import DEPENDENCY_TYPES
        if ba_version != 1 or delivery_version != 2 or len(DEPENDENCY_TYPES) != 6: raise ValueError("contract compatibility mismatch")
        return "COMPATIBLE"
    check("routers/shared contract compatibility", routers)
    def ignore_contract():
        with tempfile.TemporaryDirectory(prefix="sdlc-ignore-doctor-") as temp:
            for lane in ("docs", "app"):
                project = Path(temp) / lane
                project.mkdir()
                subprocess.run(["git", "-C", str(project), "init", "-q"], check=True)
                (project / ".gitignore").write_bytes((root / "tooling/fixtures/readiness" / (lane + ".gitignore")).read_bytes())
                check_runtime_ignores(project, lane)
        return "PASS"
    check("runtime ignore contract", ignore_contract)
    with tempfile.TemporaryDirectory(prefix="sdlc-suite-doctor-") as temp:
        project = Path(temp) / "docs"
        skills = project / ".agents/skills"
        reports = {}
        for kit in ("ba", "test"):
            def kit_check(kit=kit):
                ba_kit.install(root, skills, kit, project_root=project)
                report = ba_kit.doctor(root, skills, kit, project_root=project)
                reports[kit] = report
                if report["status"] != "READY": raise ValueError(json.dumps(report))
                return "READY"
            check(kit + " Doctor", kit_check)
        app = Path(temp) / "app"
        app.mkdir()
        report = dev_kit.doctor(root, project_root=app, mode="benchmark", spec_kit_cli=spec_kit_cli, codex_home=codex_home)
        reports["dev"] = report
        if report["status"] != "READY":
            checks.append({"name": "dev Doctor", "status": "FAIL", "detail": report})
        else:
            checks.append({"name": "dev Doctor", "status": "PASS", "detail": "READY / " + report["context_purity"]})
    if docs_project: check("docs runtime ignore", lambda: check_runtime_ignores(docs_project, "docs"))
    if app_project: check("app runtime ignore", lambda: check_runtime_ignores(app_project, "app"))
    return {"status": "FAIL" if any(row["status"] == "FAIL" for row in checks) else "READY", "checks": checks, "per_kit": reports}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("lock", "doctor"))
    parser.add_argument("--spec-kit-cli", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--docs-project", type=Path)
    parser.add_argument("--app-project", type=Path)
    args = parser.parse_args()
    if args.command == "lock":
        report = generate_lock()
    else:
        if args.spec_kit_cli is None or args.codex_home is None:
            parser.error("Doctor requires pinned --spec-kit-cli and --codex-home")
        report = doctor(spec_kit_cli=args.spec_kit_cli, codex_home=args.codex_home, docs_project=args.docs_project, app_project=args.app_project)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(1 if report.get("status") == "FAIL" else 0)
