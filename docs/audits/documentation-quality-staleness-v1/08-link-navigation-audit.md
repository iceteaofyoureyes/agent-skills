# Link and navigation audit

## Results

| Check | Result |
|---|---|
| Markdown files scanned | 431 |
| Local unresolved candidates | 36 |
| Confirmed unresolved local links | 18 |
| Confirmed broken anchors after context review | 0 |
| Unique remote URLs checked by HTTP HEAD | 58 |
| Reachable remote URLs | 56 |
| Remote 404s | 0 |
| NETWORK_UNVERIFIED | 2 |
| GitHub feature-branch URLs | 0 |
| Raw inventory ORPHAN labels | 89 |
| Actionable first-party operator/reference surfaces absent from primary indexes | 10 |

The 36 local candidates were reviewed in context: 16 are project-output paths in templates, 2 are regex snippets misread as Markdown links, 15 point to optional sibling skills absent from this repository, and 3 are in old benchmark/legacy fixtures. The confirmed 18 are documented as DOC-P3-002 and DOC-P4-002. No unresolved local navigation defect was found in the primary README/BA/Test workflow links.

The 15 missing optional sibling references occur in product-design-and-ux/SKILL.md and references/engineering-handoff.md, plus web-accessibility/SKILL.md and references/routing.md. Targets include product-discovery, product-methodology, spec-driven-development, hugo-theme, react and vite. The source may assume those separately installed skills, but the local links do not provide an alternate source.

The three historical/fixture links point from benchmark/test-kit/petclinic/fixtures/test-design-v1/inputs/baseline/02-gap-review.md, benchmark/test-kit/petclinic/foundation-v1-native-profiled/inputs/baseline/02-gap-review.md, and tooling/tests/fixtures/ba-v1-legacy-compat/02-gap-review.md to absent sibling 01-input-requirement.md files.

Two remote URLs returned HTTP 403 from ISO.org, so they are NETWORK_UNVERIFIED, not broken: https://www.iso.org/standard/72089.html and https://www.iso.org/standard/77520.html. No remote 404 was observed. Five GitHub links use pinned commit IDs for upstream source/evidence; these are immutable commit links, not feature-branch references.

## Orphan interpretation

The 89 ORPHAN rows include internal templates, progressive-disclosure skill references, raw benchmark evidence and historical design files. They are not all operator navigation defects. The first-party current surfaces absent from primary indexes are kits/dev/README.md, the seven current docs/vi/DEV_KIT_* role/reference pages (excluding the historical benchmark page), docs/vi/SDLC_SUITE_CONTRACT.md, and docs/DELIVERY_MANIFEST_V2.md. See DOC-P2-002 and DOC-P2-003.

## Method limits

The local checker handled Markdown inline links and headings. It treated template paths that describe files in a consuming project as expected project destinations. The anchor scan initially flagged punctuation/inline-code headings; each candidate was checked against its actual heading and found to resolve. External checks were read-only HEAD requests; 403 responses were left unverified.
