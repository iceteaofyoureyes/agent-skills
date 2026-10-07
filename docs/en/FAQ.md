# FAQ

## Do I need all three Kits?

No. Install the Kit needed for your role/workflow. Use all three only when you want the integrated BA → Dev → Test lifecycle.

## Can I use only Dev Kit?

Yes, when the required approved engineering/business authority already exists. Dev must not invent missing WHAT; unresolved business meaning becomes an upstream gap.

## Can I use only Test Kit?

Yes, when Test has the authority inputs required by the current Test contract. The full integrated flow may also provide Dev technical context, but Test does not gain business authority from Dev.

## Is Project Foundation another Kit?

No. It is a shared workflow/capability for creating or recovering project context.

## Can I use this on an existing project?

Yes. Brownfield recovery is a first-class use case. Current code/behavior is evidence about the existing system; it is not automatically the approved target behavior.

## Can I use it on a greenfield project?

Yes. Foundation can bootstrap target project context, while BA/Human approval still owns business behavior.

## Where does the toolkit install?

BA/Test project-scope installs use the agent's project skill directory (for Codex, `.agents/skills`). Dev/Shared runtime is installed into the explicit `--install-home` you choose. Project-owned outputs remain in the project/workflow locations defined by each Kit. See [Installation](INSTALLATION.md) before installing into an existing project.

## Can I evaluate the toolkit without installing every Kit?

Yes. Read Getting Started and the Full Flow Example first, then install only the Kit you want to try. The integrated lifecycle does not require every role to be installed on every machine.

## Does the agent approve decisions automatically?

No. \`CONTINUE\`, \`ANSWER\`, validator PASS, Doctor READY, and generated artifacts are not approval.

## What does Doctor READY mean?

The installed package and required capabilities validate. It does not mean a feature is approved, tested, passing, VERIFIED, or ready to release.

## What is READY_FOR_TEST?

A Dev handoff state. It means Engineering has produced the required implementation/review/verification evidence for Test consumption. It is not Tester verification.

## What is APPROVED_TESTWARE?

Human-approved canonical Testcases/trace. It is not automation readiness and not execution PASS.

## What is EXECUTION_READY?

Automation/execution inputs have been reviewed and bound. Tests have not necessarily run yet.

## Does every VERIFIED result require a retest?

No. A clean initial execution can go directly to Tester VERIFIED when all required observations pass and no Finding remains open. Retest is required after a defect/fix path.

## Does VERIFIED mean "merge now"?

No. VERIFIED ends the framework's product-verification lifecycle. Merge/release is a separate Human decision.

## What happens when a test command fails?

The command result is evidence. A Tester evaluates the observation against the approved oracle and classifies any Finding. A command failure is not automatically a DEFECT.

## What if Dev discovers an unclear requirement?

Dev routes an upstream gap instead of deciding business WHAT.

## Is XMind required?

No. It is an optional projection. Test core can remain usable when XMind is unavailable, as reported by the Doctor/conformance status.

## Which agent runtime is supported?

The primary verified end-to-end path is Codex-based. BA also documents Claude Code and generic installation targets. Do not assume every full cross-Kit path has equal verification on every agent runtime.

## Which Python version should I use?

Use Python **3.10+** for the documented BA/Test support baseline and the simplest full-toolkit setup. Capability-specific details are in [Installation](INSTALLATION.md).

## Where do I start if I am still confused?

Read [Getting Started](GETTING_STARTED.md), then the [Full Flow Example](FULL_FLOW_EXAMPLE.md). Only after that should most users need the deeper [Architecture](ARCHITECTURE.md) and [Readiness states](READINESS_STATES.md).
