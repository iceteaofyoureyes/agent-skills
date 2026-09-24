# BA Kit 1.0.0-rc.1

BA Kit is an AI-assisted Business Analysis workflow for clarifying requirements, separating evidence from decisions, preparing Business Rules and an SRS, and producing an Engineering Handoff after explicit Human approval. BA owns **WHAT** the system needs to do; BA Kit does not assign implementation ownership or make technical design decisions.

This is an RC1 candidate, not an accepted or public release. Packaged runtime functional acceptance is blocked by the isolated provider/runtime. See [Release Status](../../docs/RELEASE.md) and [Provenance](../../docs/PROVENANCE.md).

## Start here

- [Quick Start](../../docs/BA_KIT_QUICKSTART.md)
- [Workflow and Human Gates](../../docs/BA_KIT_WORKFLOW.md)
- [Usage Guide](../../docs/BA_KIT_USAGE_GUIDE.md)
- [CR-001 example](examples/CR-001/README.md)
- [FAQ](../../docs/BA_KIT_FAQ.md)
- [Installation](../../docs/INSTALLATION.md)

The single composition source is [`kit.yaml`](kit.yaml). The package contains one `ba-workflow` entry skill plus canonical root-level skills. Skills Manager is optional.

## Acceptance evidence

See [`acceptance.yaml`](acceptance.yaml) and [`../../ba-workflow/evals/cr001-acceptance.md`](../../ba-workflow/evals/cr001-acceptance.md). A documentation example is not packaged runtime acceptance evidence. Do not use the approved CR-001 example outputs as inputs to a fresh-session acceptance run.
