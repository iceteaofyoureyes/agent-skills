# Dev Kit VNext

Dev Kit VNext begins from an exact **Engineering Handoff VNext** backed by
`APPROVED_BASELINE` proof. BA retains business WHAT; Dev owns repository scope,
Engineering Impact V2, technical decisions and implementation HOW.

## Install and inspect

Install to a temporary user-scope home with:

```powershell
python -I tooling/install_dev_kit.py --source-root . --install-home <user-home>/.devkit
```

The installer writes `runtime/v2` and a `bin/devkit` launcher. Existing
`runtime/v1` content is retained. The launcher runs Python in isolated mode;
the package has no imports from the checkout. `devkit doctor` reports package
and capability readiness only.

Inspect the V2 contract and neutral templates:

```text
devkit schema start-request
devkit schema engineering-impact
devkit schema engineering-gap
devkit schema engineering-decision
devkit schema dev-state
devkit schema technical-approval
devkit schema dev-handoff
devkit template start-request
devkit template engineering-impact
```

V1 artifacts remain explicit read-only compatibility surfaces:
`devkit schema legacy/start-request`, `devkit schema legacy/impact-manifest`,
and `devkit schema legacy/dev-handoff`. Their authority mode is
`LEGACY_COMPAT`; they do not grant VNext authority.

## VNext workflow

```text
Engineering Handoff VNext
  → authenticate exact BA authority and revalidate Foundation proof
  → FEATURE_DELIVERY / Engineering Impact V2
  → technical plan, tasks, ED-* decisions and exact snapshot
  → Human/Tech Lead gate only when required by HIGH_RISK or active material ED
  → IMPLEMENTATION_READY → scoped source changes
  → one consolidated review and bounded blocking-fix path
  → fresh repository-scoped checks
  → exact FR/BR code and test coverage
  → Dev Handoff V2 / READY_FOR_TEST
```

The second authority mode, `TECHNICAL_MAINTENANCE`, is limited to verified
nonbehavioral maintenance evidence. It cannot authorize business behavior.
Engineering Gap pauses work until resolution evidence and a replacement
Engineering Handoff VNext are revalidated. ED-* records preserve exact
engineering decisions; required approval binds the exact technical snapshot.

Checks name a repository and execute at its bound root. Coverage is the exact
approved BR/FR set; BAREF is only a locator. Review is bounded to one full
review, one blocking-fix wave and one optional scoped rereview. `READY_FOR_TEST`
is a Dev handoff boundary, not `VERIFIED`, business acceptance or merge approval.

GitHub Spec Kit `1.0.11` is workflow state and bundle transport only. Its
feature-spec commands remain excluded; it cannot become WHAT authority or
approve a technical gate. Delivery Manifest remains
`DEFERRED_NON_AUTHORITATIVE`.

## Package records

- [Package manifest](kit.yaml)
- [V2 acceptance contract](acceptance.yaml)
- [Provenance and dependency lock](provenance.lock.json)
- [Neutral VNext outline](examples/neutral-vnext.md)
- [Engineering architecture](../../docs/vi/DEV_KIT_ARCHITECTURE.md)
- [Operational workflow](../../docs/vi/DEV_KIT_WORKFLOW.md)
