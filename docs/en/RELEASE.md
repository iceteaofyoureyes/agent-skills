# Release status

Tiếng Việt: [Trạng thái phát hành](../vi/RELEASE.md)

BA Kit 1.0.0-rc.1 is a release-candidate package, not a public release or an accepted functional release. Dev Kit and Test Kit are planned and are not implemented.

## Technical and package status

The package and installer checks have passed for Codex project installation, idempotent reinstall, Doctor READY, safe uninstall, and project isolation. Generic PowerShell/Bash installation and Claude Code structural installation have also been checked. Claude runtime acceptance was not run. These checks show the package structure and installation behavior; they do not prove the BA workflow's runtime behavior.

## Runtime functional acceptance

Packaged fresh-session CR-001 acceptance is **BLOCKED** because the isolated Codex provider/runtime returned no response. This is an environment block, not a functional PASS. Do not treat prior benchmark runs or the documentation example as acceptance of this package. Once the isolated runtime can respond, run the fresh-session cases in [kits/ba/acceptance.yaml](../../kits/ba/acceptance.yaml) and record the exact runtime and result.

## Redistribution readiness

The BA Kit payload license status is **BA_KIT_LICENSE_READY**. Every required, core, and optional skill distributed by its installer has verified provenance and the required license or attribution. This status does not mean runtime functional acceptance passed.

Whole-repository publication is **REPO_PUBLICATION_BLOCKED**. Non-BA imports still need revision-bound content and license audits, and the tracked .skills-manager metadata still needs an ownership/license or publication-scope decision. Do not describe the repository as public-release-ready before those blockers are resolved.
