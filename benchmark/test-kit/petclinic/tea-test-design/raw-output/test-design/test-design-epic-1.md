---
workflowStatus: completed
totalSteps: 5
stepsCompleted:
  - step-01-detect-mode
  - step-02-load-context
  - step-03-risk-and-testability
  - step-04-coverage-plan
  - step-05-generate-output
lastStep: step-05-generate-output
nextStep: ''
lastSaved: '2026-09-25'
---

# Test Design: Epic 1 — CR-001 Appointment Scheduling

**Date:** 2026-09-25  
**Author:** Codex benchmark  
**Status:** Draft

## Executive Summary

**Scope:** Full epic-level test design for the six approved functional requirements, FR-001 through FR-006. This document defines scenarios and validation levels; it does not generate test code or make a release decision.

**Risk summary:**

- Total risks identified: 4
- High risks (score ≥6): 0
- Critical categories: BUS, DATA

**Coverage summary:**

- P0: 0 scenarios
- P1: 13 scenario groups, 27 test cases
- P2: 1 scenario, 1 test case
- P3: 0
- Estimated future test development: ~20–32 hours; low confidence until the feature architecture and test environment are defined

## Not in Scope

| Item | Reason | Mitigation |
|---|---|---|
| Test code generation, automation, and execution | Outside this run's Test Analysis and Test Design stages | Keep the scenario design available for a separately authorized future workflow |
| XMind or Excel export | Outside the requested deliverables | Markdown plan is the source output |
| Release gate decision | No implementation or execution evidence is in scope | No PASS/CONCERNS/FAIL or release recommendation is made |
| Unapproved UI/API details and authorization behavior | The approved baseline does not define these contracts | Resolve at the appropriate design or BA checkpoint before asserting them |

## Risk Assessment

Probability and impact use TEA's 1–3 scale. The scores are initial planning estimates; no appointment defect history exists in the supplied current-system evidence.

### High-Priority Risks (Score ≥6)

None identified from the supplied requirements.

### Medium-Priority Risks (Score 3–4)

| Risk ID | Category | Evidence-grounded risk | P | I | Score | Mitigation | Owner | Timeline |
|---|---|---|---:|---:|---:|---|---|---|
| R-001 | BUS | BR-006 requires overlap checks for Scheduled appointments of the same Veterinarian and permits touching intervals. A wrong comparison can accept an overlap or reject a valid boundary booking. | 2 | 2 | 4 | Cover one true overlap, both touching directions, and a different-Veterinarian overlap at the API/integration boundary. | QA + backend owner; assign names later | Before test implementation; date TBD |
| R-002 | BUS | BR-007 and BR-008 restrict edits, reschedules, cancellation, and completion to Scheduled. A state guard error can allow a terminal Appointment to change. | 2 | 2 | 4 | Exercise the allowed Scheduled transitions and the terminal-state/action matrix once at the persistence-aware boundary. | QA + backend owner; assign names later | Before test implementation; date TBD |
| R-003 | DATA | BR-002 and BR-010 require Appointment to remain separate from Visit and completion to create exactly one Visit. A lifecycle error can omit or duplicate the Visit. | 2 | 2 | 4 | Observe the Appointment state and the count of newly created Visits after one completion. Do not assume field mapping between the records. | QA + backend owner; assign names later | Before test implementation; date TBD |
| R-004 | DATA | BR-013 requires that simultaneous booking results store only a non-conflicting Appointment. A race can persist two conflicting Scheduled appointments. | 2 | 2 | 4 | Send two overlapping same-Veterinarian create requests concurrently and verify persisted state, without asserting an unspecified response code or message. | QA + backend owner; assign names later | Before test implementation; date TBD |

### Low-Priority Risks (Score 1–2)

None identified.

## NFR Planning

No measurable security, performance, reliability, scalability, compliance, or maintainability NFR is stated in the approved BA baseline. No NFR threshold or NFR gate is proposed here. BR-013 is a functional outcome for simultaneous booking, not a throughput or latency target.

Business open items remain separate from NFRs: maximum Appointment duration is UNKNOWN; list filters, default sorting, and pagination/page size are UNKNOWN. This plan assigns no expected result to those unknowns.

## Entry Criteria

- Approved BR-001 through BR-014 and FR-001 through FR-006 remain the test oracle.
- The future Appointment API/UI and persistence contract is available before automation-level assertions are chosen.
- Test data can create known Pet and Veterinarian records and distinguish newly created Visit records.
- A controllable clock or equivalent fixture is available for the Asia/Ho_Chi_Minh future-start boundary.
- A test environment can submit concurrent create requests and inspect persisted Appointment state.

## Exit Criteria

- Every in-scope FR and relevant BR maps to at least one scenario in the coverage plan.
- Each scenario has an observable outcome and one primary test level.
- The four stated UNKNOWN areas remain unresolved in test expectations.
- No candidate release gate is run by this test-design document.

## Test Coverage Plan

Priorities describe test importance, not execution timing. P0 is empty because the baseline supplies no evidence for a critical impact with no safe workaround. P1 covers the core scheduling and lifecycle behavior; P2 covers the read-only view request.

### P0 (Critical)

None.

### P1 (High)

| Scenario | Requirement | Level | Risk Link | Count | Owner | Observable expected result |
|---|---|---|---|---:|---|---|
| TD-001 — Create and view a valid Appointment | FR-001, BR-001, BR-002, BR-003, BR-008 | E2E | R-002 | 1 | QA | A valid Appointment is saved as Scheduled with the submitted Pet, Veterinarian, start, positive duration, and reason/description; the saved Appointment can be viewed. No default duration is assumed. |
| TD-002 — Future-start boundary | FR-001, BR-004 | API | — | 3 | QA | A start equal to or before the current instant in Asia/Ho_Chi_Minh is rejected; a start strictly after it is accepted. |
| TD-003 — Positive duration | FR-001, BR-005 | API | — | 3 | QA | A positive duration is accepted; zero and negative duration are rejected. No upper-bound value or result is asserted. |
| TD-004 — Same-Veterinarian overlap and half-open boundaries | FR-002, BR-006 | API | R-001 | 3 | QA | A true overlap with another Scheduled Appointment for the same Veterinarian is rejected. A new interval starting exactly at the existing end, and one ending exactly at the existing start, are accepted under [start, end). |
| TD-005 — Pet overlap with a different Veterinarian | FR-002, BR-006, BR-012 | API | R-001 | 1 | QA | Overlapping appointments for the same Pet and different Veterinarians are not rejected solely because the Pet is the same. |
| TD-006 — Edit/reschedule a Scheduled Appointment | FR-003, BR-007, BR-008 | API | R-001, R-002 | 2 | QA | A contract-defined edit is accepted while Scheduled; a reschedule whose target overlaps its own former interval is accepted when no other Scheduled Appointment for that Veterinarian conflicts. The result remains one Appointment at the new interval. Exact editable fields come from the future interface contract. |
| TD-007 — Conflicting reschedule | FR-002, FR-003, BR-006, BR-007 | API | R-001, R-002 | 1 | QA | A target interval conflicting with another Scheduled Appointment for the same Veterinarian is not accepted. Exact error and failed-update recovery behavior are not specified by the BA baseline. |
| TD-008 — Terminal-state action guards | FR-003, FR-004, FR-005, BR-008 | API | R-002 | 8 | QA | For both Cancelled and Completed records, edit, reschedule, cancel, and complete are each disallowed. No HTTP status or message is asserted. |
| TD-009 — Cancel without hard delete | FR-004, BR-008, BR-009, BR-011 | API | R-002 | 1 | QA | Cancelling a Scheduled Appointment changes it to Cancelled and retains the same Appointment record. |
| TD-010 — Cancellation releases the time | FR-004, BR-006, BR-009 | API | R-001, R-002 | 1 | QA | After cancellation, a new Scheduled Appointment for the same Veterinarian can use the released interval. |
| TD-011 — Complete creates exactly one Visit | FR-005, BR-002, BR-008, BR-010 | API | R-002, R-003 | 1 | QA | Completing a Scheduled Appointment changes its state to Completed and creates exactly one new Visit; the Appointment remains a separate record. Visit field mapping is not asserted. |
| TD-012 — Completed Appointment does not block booking | FR-002, BR-006, BR-008 | API | R-001, R-002 | 1 | QA | A Completed Appointment does not conflict with a new Scheduled Appointment for the same Veterinarian at the same interval. |
| TD-013 — Concurrent conflicting creates | FR-002, BR-006, BR-013 | API / integration | R-001, R-004 | 1 | QA + backend owner | Of two simultaneous requests for overlapping Scheduled appointments with the same Veterinarian, persisted state contains only one of the conflicting appointments. Response code and message are not asserted. |

**P1 total:** 27 test cases. API/integration scenarios use one persistence-aware boundary; no duplicate unit, API, and E2E assertions are planned for the same business rule.

### P2 (Medium)

| Scenario | Requirement | Level | Risk Link | Count | Owner | Observable expected result |
|---|---|---|---|---:|---|---|
| TD-014 — View an Appointment | FR-006, BR-001, BR-014 | E2E (provisional) | — | 1 | QA | A saved Appointment is visible through the future Clinic Staff view. Do not assert filters, ordering, pagination, page size, or which states appear until those decisions are approved. |

**P2 total:** 1 test case.

### P3 (Low)

None.

## Execution Strategy

- **Pull request:** Run functional Appointment scenarios when implemented and when the feature suite remains under 15 minutes. Keep the state, boundary, and completion checks in the regular suite.
- **Nightly:** Include the concurrent-create scenario if the environment cannot run it deterministically on every pull request.
- **Weekly:** None proposed; no long-running performance or resilience target is in the approved baseline.

No tests were executed during this benchmark.

## Resource Estimates

These are low-confidence future test-development ranges, not estimates for this benchmark run. They assume existing PetClinic test harnesses can be reused; adjust after the Appointment interface and environment are designed.

| Priority | Cases | Estimated effort | Notes |
|---|---:|---:|---|
| P0 | 0 | N/A | No P0 scenario identified |
| P1 | 27 | ~18–30 hours | Includes persistence setup, timezone control, state cases, and concurrent request setup |
| P2 | 1 | ~2–4 hours | Depends on the future view contract |
| P3 | 0 | N/A | No P3 scenario identified |
| **Total** | **28** | **~20–34 hours (~3–5 working days)** | Requires named QA/backend owners and a test environment |

## Quality Gate Criteria

This section records TEA's test-planning thresholds only. It is not a release gate decision.

- P0 pass rate: 100%; no P0 scenarios are currently identified.
- P1 pass rate: at least 95%, with failures triaged before approval.
- P2/P3 pass rate: at least 90%, informational.
- High-risk mitigations: complete or explicitly waived; no current risk scores ≥6.
- Coverage targets: critical paths ≥80%, business logic ≥70%, edge cases ≥50%. These generic TEA targets need project-owner agreement because the BA baseline supplies no coverage percentage.
- No security or performance pass/fail threshold is assigned because no such NFR is in scope.

## Mitigation Plans

### R-001 — Same-Veterinarian conflict rule (score 4)

**Mitigation:** Cover overlapping, touching, different-Veterinarian, reschedule, cancellation-release, completed-state, and concurrent outcomes at the API/integration boundary.  
**Owner:** QA and backend owner; names TBD.  
**Timeline:** Before test implementation; date TBD.  
**Status:** Planned.  
**Verification:** TD-004 through TD-007 and TD-010, TD-012, TD-013.

### R-002 — Appointment lifecycle (score 4)

**Mitigation:** Exercise Scheduled creation, cancellation, completion, and every edit/reschedule/cancel/complete action against both terminal states.  
**Owner:** QA and backend owner; names TBD.  
**Timeline:** Before test implementation; date TBD.  
**Status:** Planned.  
**Verification:** TD-001, TD-006 through TD-011.

### R-003 — Visit cardinality (score 4)

**Mitigation:** Count new Visit records after one successful completion and verify the Appointment state independently.  
**Owner:** QA and backend owner; names TBD.  
**Timeline:** Before test implementation; date TBD.  
**Status:** Planned.  
**Verification:** TD-011.

### R-004 — Concurrent booking outcome (score 4)

**Mitigation:** Submit overlapping requests concurrently and inspect persisted state. Avoid asserting a lock, transaction, status code, or error message not specified by BA.  
**Owner:** QA and backend owner; names TBD.  
**Timeline:** Before test implementation; date TBD.  
**Status:** Planned.  
**Verification:** TD-013.

## Assumptions and Dependencies

### Assumptions and open decisions

1. The feature has no implemented Appointment code in the supplied PetClinic repositories; current source is used only to understand existing test patterns.
2. The endpoint and UI surface for the new Appointment behavior are not yet defined. API/E2E level choices are provisional and do not define an interface contract.
3. Interval tests use the start and end symbols stated in BR-006. How the implementation obtains an interval end from the Appointment data must follow the approved model/interface; this plan does not add a formula.
4. Maximum Appointment duration remains UNKNOWN. The plan does not invent a limit or expected result for values above a presumed maximum.
5. List filters, default sorting, pagination, and page size remain UNKNOWN. TD-014 checks visibility only.
6. Default duration, reason/description requiredness, response codes/messages, authorization mapping, and Visit field mapping are not defined by this baseline and receive no expected result here.

### Dependencies

1. Final Appointment API/UI and persistence contracts — required before implementation-level assertions.
2. Stable test clock and timezone fixture — required before testing BR-004.
3. Concurrent-request-capable test environment — required before executing TD-013.
4. BA resolution of open items only if tests need to assert those behaviors.

## Current-System Context (Supplemental Only)

The supplied current-system repositories contain Angular component/service specs and Spring REST/controller/service tests. No Appointment implementation or Appointment-named test was found in either repository. The existing Visit model contains a date, description, and Pet relation; this is not an Appointment requirement and does not define which fields a new Visit receives when an Appointment is completed.

## Interworking and Regression

| Current component | Impact | Regression scope |
|---|---|---|
| Spring Petclinic REST backend | Supplemental source evidence only; Appointment endpoints are not present | Reuse the existing backend service/controller test style once an Appointment design exists |
| Spring Petclinic Angular frontend | Supplemental source evidence only; Appointment UI is not present | Reuse the existing Angular component/service test style once a view contract exists |
| Visit | FR-005/BR-002/BR-010 require a separate Visit after completion | Verify one new Visit and Completed Appointment state; do not assume field mapping |

## Follow-on Workflows (Manual)

TEA's ATDD or automation workflows are separate. They were not invoked because this run ends at Test Design and the feature is not implemented.

## Approval

**Test Design Approved By:** Not approved; draft benchmark output.

## Appendix

### Knowledge base references

- risk-governance.md
- probability-impact.md
- test-levels-framework.md
- test-priorities-matrix.md

### Related documents

- Approved Business Rules: kits/ba/examples/CR-001/vi/03-approved-business-rules.md
- Approved SRS excerpt: kits/ba/examples/CR-001/vi/04-srs-excerpt.md
- Engineering handoff: kits/ba/examples/CR-001/vi/05-engineering-handoff.yml
- Epic-shaped adapter: input-adapter/epic-1.md

**Generated by:** BMad TEA Agent — Test Architect Module  
**Workflow:** bmad-testarch-test-design  
**Source version:** upstream commit 1f53e9095061ab66f3c35abd9b98baf0f50cf8fe
