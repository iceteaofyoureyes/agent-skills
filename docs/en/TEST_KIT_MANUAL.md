# Manual Test VNext — English overview

In the integrated suite, Test starts after Dev publishes READY_FOR_TEST. Its business authority is the exact Engineering Handoff VNext backed by an approved BA baseline. Dev Handoff V2 carries technical context; it cannot redefine business behavior. The [Test manifest](../../kits/test/kit.yaml) is the machine source for package identity and required capabilities.

## Manual flow

~~~
Approved Engineering Handoff
→ canonical Test Design
→ Human Design review → APPROVED_DESIGN
→ canonical Testcases
→ Human Case review → APPROVED_TESTWARE
~~~

The Human approves each exact design and testcase snapshot through the trusted host. Validator PASS, generated output, Test Doctor READY, or an agent callback cannot approve either gate. Trace canonical behavior to BR-* and FR-*; BAREF is a locator only. Keep UNKNOWN or deferred behavior visible, and leave material execution dependencies OPEN until resolved.

APPROVED_TESTWARE is the manual lane output. It is not automation readiness, EXECUTION_READY, execution PASS, or VERIFIED. Continue through [Automation V1](TEST_AUTOMATION_V1.md), then [Execution VNext](TEST_EXECUTION_VNEXT.md).

## Start and recover

Use the Vietnamese primary [Quick Start](../vi/TEST_KIT_QUICKSTART.md), [capabilities](../vi/TEST_KIT_CAPABILITIES.md), [workflow and Human Gates](../vi/TEST_KIT_WORKFLOW.md), and [usage scenarios](../vi/TEST_KIT_USAGE_GUIDE.md). Install and check the package with [Installation](INSTALLATION.md); recovery paths are in [Troubleshooting](TROUBLESHOOTING.md).

V1 examples are LEGACY_COMPAT and read-only. The current neutral example is [here](../../kits/test/examples/vnext/neutral/README.md). Delivery Manifest is DEFERRED_NON_AUTHORITATIVE and is not a prerequisite.
