"""Create a dedicated pinned agent context; never copy credentials or global hooks."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def prepare(source, destination, *, foundation=False):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError("profile destination must be fresh")
    destination.mkdir(parents=True)
    names = ("requirements-gap-auditor", "verification-before-completion", "dev-kit")
    if foundation:
        names += ("project-foundation",)
    for name in names:
        shutil.copytree(source / name, destination / "skills" / name)
    shutil.copytree(source / "kits/dev/plugin", destination / "pinned-source/agent-skills-dev-kit")
    market = destination / ".agents/plugins/marketplace.json"
    market.parent.mkdir(parents=True)
    data = json.loads((source / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    data["plugins"][0]["source"]["path"] = "./pinned-source/agent-skills-dev-kit"
    market.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (destination / "config.toml").write_text('[plugins."agent-skills-dev-kit@agent-skills-dev-kit"]\nenabled = true\n', encoding="utf-8")
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    inventory = {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(destination.rglob("*")) if p.is_file()}
    record = {"schema_version": 1, "agent_skills_commit": commit, "intended_lane": "DEV",
              "profile_environment_variable": "CODEX_HOME", "files": inventory,
              "credentials": "HOST_MANAGED_NOT_COPIED", "golden_run": "NOT_STARTED"}
    (destination / "profile-lock.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def register(destination):
    destination = Path(destination).resolve()
    command = shutil.which("codex.cmd") if os.name == "nt" else shutil.which("codex")
    if not command:
        raise ValueError("Codex host is required to register the isolated Dev profile")
    env = dict(os.environ, CODEX_HOME=str(destination))
    for args in (["plugin", "marketplace", "add", str(destination)], ["plugin", "add", "agent-skills-dev-kit@agent-skills-dev-kit"]):
        subprocess.run([command, *args], env=env, check=True, capture_output=True)
    record_path = destination / "profile-lock.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["files"] = {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(destination.rglob("*")) if p.is_file() and p != record_path}
    record["native_plugin_registration"] = "INSTALLED"
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--foundation", action="store_true", help="Include Project Foundation in this explicitly expanded profile")
    args = parser.parse_args()
    record = prepare(args.source, args.destination, foundation=args.foundation)
    if args.register:
        record = register(args.destination)
    print(json.dumps(record, indent=2))
