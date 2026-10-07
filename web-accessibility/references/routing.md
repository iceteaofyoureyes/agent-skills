# Routing

Keep the semantic and interaction contract framework-agnostic first. Then use the current official documentation for the chosen framework or component library to implement it; do not assume a universal framework or library.

| Situation | Route |
|---|---|
| Hugo template architecture, theme-wide layout, or CMS rendering | Optional separately installed hugo-theme skill and design/accessibility reference; not bundled here |
| Stakeholder evidence and validation | Optional separately installed product-discovery skill; not bundled here |
| Product scope, priority, or rationale | Optional separately installed product-methodology skill; not bundled here |
| User-facing behavior, task flows, state/recovery models, or engineering UX handoff | [product-design-and-ux](../../product-design-and-ux/SKILL.md); keep accessibility conformance depth here |
| Browser platform behavior | WHATWG HTML in `source-index.md` |
| ARIA roles/pattern contracts | WAI-ARIA 1.2 and APG in `source-index.md` |
| Framework-specific component API | Current official documentation after requirements are defined |

Do not route to a library merely because it advertises accessibility. Confirm its behavior against the user task and target browser/AT support.
