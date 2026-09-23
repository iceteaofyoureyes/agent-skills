# Installation

From a project checkout:

```powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git
cd agent-skills
.\tooling\install.ps1 ba --agent codex --scope project
.\tooling\doctor.ps1 ba --agent codex --scope project
```

```bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git
cd agent-skills
./tooling/install.sh ba --agent codex --scope project
./tooling/doctor.sh ba --agent codex --scope project
```

Project install copies skills to the current workspace's native skill directory. Codex uses `.agents/skills`; Claude Code uses `.claude/skills`. User installs use Codex's `~/.agents/skills` and Claude Code's `~/.claude/skills`. These locations follow the [OpenAI skill guide](https://learn.chatgpt.com/docs/build-skills) and [Claude Code skills guide](https://code.claude.com/docs/en/skills).

For a generic Agent-Skills-compatible agent, pass an explicit destination:

```powershell
.\tooling\install.ps1 ba --agent generic --target C:\path\to\agent\skills
```

```bash
./tooling/install.sh ba --agent generic --target /path/to/agent/skills
```

Use `--scope user` for a user-level install or `--scope project` for an isolated project install. Generic mode requires `--target`. `--target` also overrides a native agent path for isolated testing. Python 3.8+ is required; no Python packages, Skills Manager, Codex profile or global agent configuration changes are required.

Install reads all dependencies from `kits/ba/kit.yaml`, copies only missing skill directories, and never overwrites an existing skill. Repeating the command leaves unchanged BA-managed skills untouched. If a same-name folder already exists, it is preserved and reported; the kit does not merge two skills with the same name.

Uninstall:

```powershell
.\tooling\uninstall.ps1 ba --agent codex --scope project
```

```bash
./tooling/uninstall.sh ba --agent codex --scope project
```

Uninstall removes only unchanged BA-managed skill directories listed in `.ba-kit-install.json`. Modified folders and skills referenced by another `.*-kit-install.json` are preserved and reported. It never edits agent configuration or authentication. Run Doctor after installation:

```powershell
.\tooling\doctor.ps1 ba --agent codex --scope project
```

Skills Manager remains optional. This environment had no Skills Manager CLI, so existing `.skills-manager/` metadata was left untouched; canonical BA Kit install and Doctor do not read it.
