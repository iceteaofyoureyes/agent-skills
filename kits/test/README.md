# Test Kit V1

**Test Kit = HOW DO WE PROVE IT.** Test Kit V1 turns an approved BA baseline into reviewed manual testware. The Human owns both approval gates.

```text
Approved BA Baseline
→ TEA analysis
→ Canonical Test Design
→ Human Design Gate
→ Canonical Testcases
→ Human Case Gate
→ APPROVED_TESTWARE
→ STOP_V1
```

Optional, Human-triggered projections are one-way views of the canonical artifacts:

```text
Canonical Test Design → XMind projection
Canonical Testcases   → Excel projection
```

Automation planning, execution, triage, and evidence automation are **Automation Test V2** and are not included in V1.

## Bắt đầu

The full operator guides are maintained in the source repository and are not copied into the install. This README is self-contained for the installed context. Browse the [Agent Skills repository](https://github.com/iceteaofyoureyes/agent-skills); from a checkout, the detailed guides are at:

- Quick Start — `docs/vi/TEST_KIT_QUICKSTART.md`
- Capabilities and boundaries — `docs/vi/TEST_KIT_CAPABILITIES.md`
- Usage Guide — `docs/vi/TEST_KIT_USAGE_GUIDE.md`
- Workflow and Human Gates — `docs/vi/TEST_KIT_WORKFLOW.md`
- CR-001 example — `kits/test/examples/CR-001/README.md`
- [Installation and troubleshooting](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/INSTALLATION.md) — `docs/vi/INSTALLATION.md`
- [Provenance and licenses](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/PROVENANCE.md) — `docs/vi/PROVENANCE.md`
- [Release status](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/RELEASE.md) — `docs/vi/RELEASE.md`
- English overview — `docs/en/TEST_KIT_README.md`

## Prerequisites and install

Test Kit V1 supports Codex project scope. Use Python 3.10+, Codex CLI, and a project `_bmad/tea/config.yaml` compatible with the pinned TEA skill. The pinned TEA and Katalon skills are bundled; installation does not download dependencies. Codex resolves from `TEST_KIT_CODEX_COMMAND`, then `PATH`, and fails closed if an explicit override is invalid.

From the target project, invoke the scripts in your Agent Skills checkout:

```powershell
& '<path-to-agent-skills>\tooling\install.ps1' test --agent codex --scope project
& '<path-to-agent-skills>\tooling\doctor.ps1' test --agent codex --scope project
```

```bash
<path-to-agent-skills>/tooling/install.sh test --agent codex --scope project
<path-to-agent-skills>/tooling/doctor.sh test --agent codex --scope project
```

Doctor verifies the installed package and reports local drift or corrupt metadata. Reinstall preserves locally edited managed files; it does not adopt those edits as the expected package bytes. Uninstall removes unchanged Test-owned files and preserves unrelated project files. See [Installation](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/INSTALLATION.md) for details.

## Workflow and projections

TEA analysis is advisory. The adapter creates and validates Canonical Test Design, then stops for Human review at `DESIGN_REVIEW`. After an authenticated approval for that exact snapshot, the pinned Katalon skill generates cases; the adapter validates Canonical Testcases and stops at `CASE_REVIEW`. Only a valid Human approval receipt with no material open execution dependency produces `APPROVED_TESTWARE` and `STOP_V1`. Outputs and evidence belong in a project-owned run directory.

XMind uses its pinned presentation profile and does not accept a Human-supplied template; ambiguous mapping returns `CANNOT_PROJECT_HUMAN_PROFILE`. Excel supports `HUMAN_SUPPLIED_APPROVED_TEMPLATE → PROJECT_TEMPLATE → DEFAULT_TEMPLATE`; ambiguous mapping returns `CANNOT_PROJECT_TEMPLATE`. XMind needs Node.js/npm and its pinned SDK; Excel needs the hash-locked Python projection dependencies. Bootstrap either capability explicitly only when requested. Both projections leave canonical artifacts and gate state unchanged.

## V1 boundary

V1 produces reviewed Test Design and manual testcases, with optional XMind and Excel projections. It does not execute tests, produce execution evidence, triage failures, or automate defects. Those capabilities belong to **Automation Test V2**.
