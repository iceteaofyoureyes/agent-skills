# Full Flow Example

This example is intentionally small. Its purpose is to show **who decides what**, not to demonstrate every schema field.

## Change request

> Add text search and multi-status filtering to the Project List.

Assume this is an existing web application.

## 1. Foundation — recover enough context

The project lacks reliable documentation for the Project List.

Foundation records:

- where the current screen/service lives;
- what is confirmed about the current system;
- what is inferred rather than confirmed;
- what is still unknown;
- the relevant repository boundaries.

Foundation does **not** decide the new search behavior.

## 2. BA Kit — define WHAT

BA review finds questions such as:

- Which fields are searchable?
- Is search case-sensitive?
- Can several statuses be selected?
- When text and status are both supplied, is the relationship AND or OR?
- What should the empty state mean?

The Human answers. BA turns those decisions into traceable Business Rules / Functional Requirements and produces an exact approved baseline.

~~~text
Requirement
→ clarification
→ BR / FR
→ canonical SRS
→ Human approval
→ Engineering Handoff
~~~

At this point the WHAT is approved. Repository ownership and implementation design are still Engineering concerns.

## 3. Dev Kit — decide HOW and implement

Dev consumes the approved Engineering Handoff and determines:

- affected repositories/components;
- implementation ownership;
- technical risks;
- material engineering decisions;
- build/static/unit/integration checks.

If Dev discovers an unclear business rule, it stops and reports an upstream requirement gap (\`UPSTREAM_GAP\`); it does not invent WHAT.

After implementation and engineering verification:

~~~text
Dev → READY_FOR_TEST
~~~

This means engineering work is ready for Test consumption. It does not mean the feature is VERIFIED.

## 4. Test Kit — design proof

Test creates coverage from the approved BR/FR set:

~~~text
Test Design
→ Human Design Gate
→ APPROVED_DESIGN
→ Testcases
→ Human Case Gate
→ APPROVED_TESTWARE
~~~

Automation is planned only after approved testware.

~~~text
APPROVED_TESTWARE
→ Automation Plan
→ implementation/review
→ EXECUTION_READY
~~~

\`EXECUTION_READY\` means execution inputs are bound. It does not mean tests already ran or passed.

## 5A. Clean first execution

Suppose every required automated/manual Testcase has a PASS Observation and no Finding remains open.

~~~text
EXECUTION_READY
→ Execution
→ all required observations PASS
→ authenticated Tester
→ VERIFIED
~~~

No retest is required for this clean initial pass.

## 5B. Defect path

Suppose the filter returns archived items incorrectly.

The Tester records the Observation and classifies the Finding. If it is a product defect:

~~~text
Finding
→ DEFECT
→ defect handoff to Dev (DEFECT_READY_FOR_DEV)
→ Dev Fix
→ fresh engineering verification
→ READY_FOR_RETEST
→ Tester retest
   ├─ PASS → VERIFIED
   └─ FINDING → REOPENED
~~~

A failing command alone is not automatically a DEFECT. Test classifies the observation against the approved oracle.

## Other Finding routes

Not every Finding goes to Dev as a defect:

- \`SPEC_GAP\` → requirement/spec authority;
- \`BUSINESS_DECISION_REQUIRED\` → Human/business authority;
- \`TEST_ISSUE\` → Test owner;
- \`ENVIRONMENT_ISSUE\` → environment/operations owner.

## What the Human still controls

Human authority is required where the workflow defines approval:

- business baseline;
- Test Design;
- Testcases;
- material technical decisions when policy/risk requires it;
- final merge/release decision.

An agent, validator, Doctor, or generated artifact cannot self-approve.

## What to read next

- [Getting Started](GETTING_STARTED.md)
- [Architecture](ARCHITECTURE.md)
- [Readiness states](READINESS_STATES.md)
