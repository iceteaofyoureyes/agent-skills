"""Create a dedicated pinned agent context; never copy credentials or global hooks."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def prepare(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError("profile destination must be fresh")
    destination.mkdir(parents=True)
    for name in ("requirements-gap-auditor", "verification-before-completion", "dev-kit"):
        shutil.copytree(source / name, destination / "skills" / name)
    shutil.copytree(source / "kits/dev/plugin", destination / "plugins/agent-skills-dev-kit")
    market = destination / ".agents/plugins/marketplace.json"
    market.parent.mkdir(parents=True)
    data = json.loads((source / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    data["plugins"][0]["source"]["path"] = "./plugins/agent-skills-dev-kit"
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination), indent=2))
