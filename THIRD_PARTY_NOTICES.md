# Third-party notices

This index records third-party components and license locations. Third-party skill license files travel inside the copied skill directories. The root LICENSE applies only to project-owned content; third-party components keep their original licenses and notices. See [docs/en/PROVENANCE.md](docs/en/PROVENANCE.md) for evidence.

## BA Kit core and required skills

### codebase-discovery

- Component: BA Kit core skill
- Source: https://github.com/DiUS/agent-toolkit/tree/d43b664e2860f7a5dd5b8ae892c44fdfc5ae9dfc/skills/codebase-discovery
- License: MIT
- Copyright: Copyright (c) 2026 DiUS
- Local changes: none to skill files; Bryan Signey attribution remains
- License location: codebase-discovery/LICENSE

### verification-before-completion

- Component: BA Kit core skill
- Source: https://github.com/obra/superpowers/tree/3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b/skills/verification-before-completion
- License: MIT
- Copyright: Copyright (c) 2025 Jesse Vincent
- Local changes: none to skill content; line endings normalized
- License location: verification-before-completion/LICENSE

### requirements-gap-auditor, requirements-interrogator, business-rule-extractor

- Source: https://github.com/45ck/business-analysis-skills
- Source paths: .agents/skills/requirements-gap-auditor/SKILL.md; .agents/skills/requirements-interrogator/SKILL.md; .agents/skills/business-rule-extractor/SKILL.md
- Revision: 1fe1950bc4759e732b036c562b0cff99675e1695
- License: MIT
- Copyright: Copyright (c) 2026; the source notice names no holder
- Local changes: Agent Skills description frontmatter only; normalized bodies are identical
- License locations: each skill directory contains LICENSE

### requirements-quality-check

- Source: https://github.com/45ck/business-analysis-skills
- Source path: quality/requirements-quality-check/SKILL.md
- Revision: 6114b14d939622ff38b971198e2f064ac1aa11df
- License: MIT
- Copyright: Copyright (c) 2026; the source notice names no holder
- Local changes: name and description frontmatter; normalized body is identical
- License location: requirements-quality-check/LICENSE

### document-docx

- Source: https://github.com/vasilyu1983/AI-Agents-public/tree/da9d28fd0f5427f18a15d3fb363ab3651e6625ca/frameworks/shared-skills/skills/document-docx
- License: MIT
- Copyright: Copyright (c) 2025-2026 Vasiliy Uvarov
- Local changes: learning files and generated caches removed; learning workflow and related skills made optional; unavailable sibling links removed; two scripts differ only by a trailing blank line
- License location: document-docx/LICENSE

### drawio-skill

- Source: https://github.com/Agents365-ai/drawio-skill/tree/7aa92f73819766eb914fffac66762cf2adb5d828/skills/drawio-skill
- License: MIT
- Copyright: Copyright (c) 2026 Agents365-ai
- Local changes: none; upstream LICENSE retained
- License location: drawio-skill/LICENSE

## BA Kit optional skills

### product-design-and-ux, web-accessibility

- Source: https://github.com/magnus919/agent-skills
- Revisions: product-design-and-ux 035e58d3e39690361596901ab8f17222ab9baf02; web-accessibility f7819d0f2048d1b71e0c261c660476965aa26602
- License: MIT
- Copyright: Copyright (c) 2026 Magnus Hedemark
- Local changes: none to skill files
- License locations: each skill directory contains LICENSE

### frontend-design

- Source: https://github.com/anthropics/skills/tree/34040c9c568585f6929bedeaad110ad08f079624/skills/frontend-design
- License: Apache-2.0
- Copyright: the upstream skill LICENSE.txt names no copyright holder
- Local changes: none
- License location: frontend-design/LICENSE.txt

### impeccable

- Source: https://github.com/pbakaus/impeccable
- Revision: 53 files from cd12f8660e2dde57b9615c8a6b8ea674101f9cfc; adapt.md, audit.md, and harden.md from 6a93a352936ac7fbb1898a239ddae1f8c3828150
- License: Apache-2.0
- Copyright: Copyright 2025 Paul Bakaus
- Local changes: mixed 4.3.1 and 4.4.0 skill files; upstream notice retained for ehmo platform-design-skills material
- License and notice: impeccable/LICENSE; impeccable/NOTICE.md

### playwright

- Source: https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/playwright
- License: Apache-2.0
- Copyright: Copyright (c) Microsoft Corporation
- Local changes: LICENSE.txt line endings only
- Attribution: NOTICE.txt retains microsoft/playwright-cli and skills/playwright-cli/SKILL.md; that source revision is not recorded there
- License and notice: playwright/LICENSE.txt; playwright/NOTICE.txt

## Other repository components

### XMind JavaScript SDK

- Component: optional Test Kit V1 XMind projection serializer
- Package: `xmind@2.2.33` (exact; lockfile in `tooling/xmind/package-lock.json`)
- Source: https://github.com/xmindltd/xmind-sdk-js/tree/e5f8a6cfde44b813967471a8e0bdde33c1747cc1
- npm integrity: `sha512-0+kolKxRcif0v4EFFE6Tl+7mPlp7s4t4gHZl8PXWY05M469TFqwHWk9eaPfAeCL5GmeQGTWVoA5+rmj779thCg==`
- License: MIT; Copyright (c) 2019 - 2023 Xmind Ltd.
- Local adaptation: exporter and SDK bridge are project-owned; upstream SDK implementation is not copied
- License location: installed npm package `xmind/LICENSE`

### Excel projection Python dependencies

- `openpyxl==3.1.5` (`tooling/requirements-excel.lock`)
  - Upstream: https://foss.heptapod.net/openpyxl/openpyxl, release `3.1.5`; PyPI: https://pypi.org/project/openpyxl/3.1.5/
  - License: MIT
  - Wheel integrity: `sha256:5282c12b107bffeef825f4617dc029afaf41d0ea60823bbb665ef3079dc79de2`
- `et-xmlfile==2.0.0` (openpyxl runtime dependency; `tooling/requirements-excel.lock`)
  - Upstream: https://foss.heptapod.net/openpyxl/et_xmlfile, release `v2.0.0`; PyPI: https://pypi.org/project/et-xmlfile/2.0.0/
  - License: MIT
- Wheel integrity: `sha256:7a91720bc756843502c3b7504c77b8fe44217c85c537d85037f0f536151b2caa`

### BMAD TEA runtime pin test fixture

- Component: byte-exact upstream fixture used to test the pinned TEA runtime inventory
- Source: `bmad-code-org/bmad-method-test-architecture-enterprise`, commit `1f53e9095061ab66f3c35abd9b98baf0f50cf8fe`
- Source path: `src/workflows/testarch/bmad-testarch-test-design/`
- Local fixture: `tooling/tests/fixtures/tea-test-design-v1/`; per-file SHA-256 values are in `tooling/pins/tea-test-design-v1.json`
- License: MIT; Copyright (c) 2025 BMad Code, LLC
- License location: `tooling/tests/fixtures/tea-test-design-v1.LICENSE`
- Local changes: none to upstream fixture bytes

### webapp-testing

- Source: https://github.com/anthropics/skills/tree/34040c9c568585f6929bedeaad110ad08f079624/skills/webapp-testing
- License: Apache-2.0
- Copyright: Copyright 2026 Anthropic, PBC
- Local changes: none
- License location: webapp-testing/LICENSE.txt

srs-function-document is now a project-owned behavioral reimplementation under MIT; the previous unknown-origin implementation was replaced and its origin was not recovered. See docs/en/PROVENANCE.md. Other non-BA skill imports and the tracked .skills-manager metadata still need provenance/license decisions before whole-repository redistribution.
