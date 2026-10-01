# Test Kit V1.1 — English overview

**Test Kit answers “How do we prove it?”** It turns a Human-approved BA baseline into a canonical Test Design and manual testcases, with a separate authenticated Human gate for each. It does not redefine business requirements or decide implementation architecture.

```text
Approved BA Baseline → TEA analysis → Canonical Test Design
→ Human Design Gate → Canonical Testcases
→ Human Case Gate → APPROVED_TESTWARE → STOP_V1
```

V1.1 adds project-owned, hash-bound testing policy as non-authoritative guidance for Design and Cases; see the [Vietnamese customization guide](../vi/TEST_KIT_CUSTOMIZATION.md). The full operator documentation is currently in Vietnamese: [Quick Start](../vi/TEST_KIT_QUICKSTART.md), [capabilities](../vi/TEST_KIT_CAPABILITIES.md), [scenario guide](../vi/TEST_KIT_USAGE_GUIDE.md), [workflow and gates](../vi/TEST_KIT_WORKFLOW.md), and the [CR-001 example](../../kits/test/examples/CR-001/README.md). This page is an English entrypoint, not a full translation of those guides.

## Install

Test Kit V1.1 supports Codex project scope. From the target project, with Python 3.10+ and Codex CLI available:

```powershell
& 'C:\tools\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
```

```bash
~/src/agent-skills/tooling/install.sh test --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh test --agent codex --scope project
```

The project also needs a TEA-compatible `_bmad/tea/config.yaml`. The package bundles pinned TEA and Katalon skills. Native generation resolves `TEST_KIT_CODEX_COMMAND` first, then Codex on `PATH`; an invalid explicit override fails closed. Installation does not silently download optional dependencies. See [installation](../vi/INSTALLATION.md).

## Authority and Human gates

An approved engineering handoff and its hashed Business Rules, SRS, and decisions define business behavior. TEA is advisory analysis; the validated **Canonical Test Design** is the coverage artifact. Katalon is a pinned generator input; the validated **Canonical Testcases** are the manual testcase artifact. `REVIEW` and `ANSWER` do not approve anything. `CONTINUE`, “Next”, “OK”, and “PASS” do not approve anything. Only an authenticated Human `APPROVE` receipt bound to the current artifact revision, semantic hash, and upstream refs can pass the corresponding gate. `REQUEST_CHANGES` opens a new draft revision.

Unknown BA behavior stays `UNKNOWN`. A deferred scenario does not acquire an invented expected result. P0–P3 are advisory test priorities, not business rules or execution results. A material open execution dependency blocks Case Gate approval.

## Optional projections and V1.1 limit

XMind is a one-way view of approved Canonical Test Design, using the pinned Logic Chart Right presentation profile. Excel is a one-way view of approved Canonical Testcases, with one testcase per row by default. External projection manifests retain trace and hashes. Neither file is canonical, and V1 does not import edits back into Test Design or Testcases.

Excel can inspect a Human-supplied or project `.xlsx` template before using the default. XMind V1 has **no supplied-template API**; a requested Human XMind template cannot be treated as supported. Optional XMind uses a pinned npm lockfile; optional Excel uses hash-locked Python requirements.

`TEST_ONLY` fixtures and outputs are non-production evidence. Automation planning, code generation, Playwright/API execution, execution evidence, flaky management, failure triage, and automated defect handling belong to **Automation Test V2**. Framework acceptance does not approve a project's testware. See [release status](../vi/RELEASE.md).
