"""Internal intent preparation, using project-owned quality gates and delivery authority."""
import argparse
import json
import subprocess
from pathlib import Path

from . import dev_kit as dev
from delivery_manifest import load_delivery_manifest


def derive_checks(project):
    project = Path(project)
    owned = project / "quality-gate.json"
    if owned.is_file():
        checks = json.loads(owned.read_text(encoding="utf-8"))["checks"]
        return checks
    package = project / "package.json"
    if package.is_file():
        scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        if "qa:gate" in scripts and "build" in scripts:
            return [{"name": "build", "category": "build", "argv": ["npm", "run", "build"]},
                    {"name": "qa:gate", "category": "tests", "argv": ["npm", "run", "qa:gate"]}]
    raise ValueError("repository-owned deterministic build/test quality gate is missing")


def start_from_delivery(project, delivery_path, summary):
    project = Path(project).resolve()
    if not (project / "AGENTS.md").is_file():
        raise ValueError("target AGENTS.md is required")
    delivery = load_delivery_manifest(delivery_path)
    targets = delivery["data"]["targets"]
    if len(targets) != 1:
        raise ValueError("multiple targets require cross-repository impact planning")
    target = targets[0]
    origin = subprocess.check_output(["git", "-C", str(project), "remote", "get-url", "origin"], text=True).strip()
    if not origin.removesuffix(".git").endswith("/" + target["repository"]) and not origin.removesuffix(".git").endswith(":" + target["repository"]):
        raise ValueError("target repository does not match delivery routing")
    actual = subprocess.check_output(["git", "-C", str(project), "rev-parse", "HEAD"], text=True).strip()
    change_id = delivery["data"]["feature"]["id"] + "-DEV-" + delivery["sha256"][:8]
    run = project / dev.RUNS_DIR / change_id
    if run.is_dir():
        _, inputs = dev._load_run(project, change_id)
        return {"status": "RESUMED", "run_dir": str(run), "route": inputs["route"]}
    if actual != target["base_revision"]:
        raise ValueError("target base revision differs from delivery manifest")
    files = subprocess.check_output(["git", "-C", str(project), "ls-files"], text=True).splitlines()
    request = {"schema_version": 1, "change_id": change_id, "kind": "feature", "summary": summary,
               "signals": [], "baseline": str(delivery["baseline"].handoff_path), "checks": derive_checks(project)}
    internal = project / ".devkit/start-request.json"
    dev.write_artifact(internal, request)
    validated = dev.load_start_request(internal)
    started = dev.start_run(project, **validated)
    inputs = dev._read_json(Path(started["run_dir"]) / "input.json")
    inputs["delivery_snapshot"] = {"path": str(delivery["path"]), "sha256": delivery["sha256"]}
    inputs["provisional_write_scope"] = [target["module"]]
    inputs["inspection"] = {"tracked_files": files, "agents_read_required": True}
    dev._write_run_json(Path(started["run_dir"]), "input.json", inputs, inputs["baseline_snapshot"])
    return {"status": "STARTED", **started}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    print(json.dumps(start_from_delivery(args.project_root, args.delivery, args.summary), indent=2))


if __name__ == "__main__":
    main()
