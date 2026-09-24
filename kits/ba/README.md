# BA Kit 1.0.0-rc.1

BA Kit owns business requirements, evidence classification, questions, Business Rules, SRS, diagrams and the approved engineering handoff. It does not make technical design or implementation-ownership decisions.

Install with Codex, Claude Code, or an explicit generic skills directory using the commands in [`../../docs/INSTALLATION.md`](../../docs/INSTALLATION.md). Skills Manager is optional.

The single composition source is [`kit.yaml`](kit.yaml), valid JSON syntax within YAML 1.2. Do not add a second dependency list to installers. The package contains one `ba-workflow` orchestrator plus its root-level atomic skills.

## Acceptance

See [`acceptance.yaml`](acceptance.yaml), [`examples/README.md`](examples/README.md), and [`../../ba-workflow/evals/cr001-acceptance.md`](../../ba-workflow/evals/cr001-acceptance.md). `READY_FOR_ACCEPTANCE` is not a 1.0.0-rc.1 PASS; a reviewer must run fresh-session CR-001 acceptance.
