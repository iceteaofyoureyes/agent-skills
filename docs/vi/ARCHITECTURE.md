# Tổng quan kiến trúc

## Mục tiêu

BA Kit tổ chức các atomic skills thành một workflow cho BA mà vẫn giữ Human làm business authority.

~~~text
BA Kit = WHAT
Dev Kit = WHERE / WHO OWNS + HOW
  ├── Engineering Impact = WHERE / WHO OWNS
  └── repo-local Spec Kit + engineering capabilities = HOW
Test Kit + TEA = HOW DO WE PROVE IT
~~~

## Layer

~~~text
User intent
    ↓
ba-workflow
    ↓
state / authority / gate / route
    ↓
atomic capabilities
    ├── discovery
    ├── requirement review
    ├── Business Rules
    ├── SRS
    ├── DOCX
    ├── Draw.io
    └── optional UX/UI/prototype
~~~

BA Kit hiện dùng atomic skills canonical ở repository root. Dev Kit V1 đang thiết kế package theo kit-scoped Agent Plugin để giữ nguyên upstream skill layout/resources khi cần. Mỗi Kit vẫn phải có một composition manifest duy nhất làm source of truth; không được để global/user skills ngầm trở thành dependency.

## Semantic, visual và delivery authority

BA workflow tách ba lớp để tránh artifact presentation ghi đè business truth:

~~~text
SEMANTIC
Confirmed BA Decisions
+ Approved Business Rules
+ Canonical SRS

VISUAL
Approved Figma / screenshot / diagram / prototype
(chỉ visual/interaction meaning được xác nhận)

DELIVERY
Selected Word template

AS-IS
CURRENT_SYSTEM evidence
~~~

DOCX, Draw.io và prototype là derived artifacts; semantic change phải quay về semantic authority trước.

## Project modes

- brownfield;
- greenfield;
- document-only;
- visual-assisted.

Workflow không bắt mọi request chạy full pipeline; nó bắt đầu từ earliest safe checkpoint.

## Responsibility flow

| Stage | Question | Status |
|---|---|---|
| BA Kit | **WHAT**? | RC1 candidate; remediation |
| Dev Kit / Engineering Impact | **WHERE / WHO OWNS**? | V1 foundation in development |
| Dev Kit / Spec Kit + engineering capabilities | **HOW**? | V1 foundation in development |
| Test Kit + TEA | **HOW DO WE PROVE IT**? | Planned |

~~~text
Requirement
→ BA Kit
→ Approved BA Baseline
→ Dev Kit
   → Spec Readiness
   → Engineering Impact
   → repo-local Spec Kit / implementation / review / verification
→ Test Kit + TEA
→ Human Final Acceptance
~~~

## Required vs optional

BA Kit required capabilities bao gồm discovery, requirement review, Business Rules, SRS, DOCX và Draw.io. UX/UI/prototype/browser/accessibility capabilities là optional.

Xem [Khả năng BA Kit](BA_KIT_CAPABILITIES.md).

## Installer architecture

Installer đọc dependency từ **kits/ba/kit.yaml**.

- Codex/Claude Code: cài vào Agent Skills directory tương ứng;
- generic: explicit target directory;
- Skills Manager: optional, không phải runtime dependency.

## Handoff boundary

Engineering Handoff chỉ xuất hiện sau explicit BA approval và không chứa:

- repository/module owner;
- FE/BE/service owner;
- API/event shape;
- DB schema;
- architecture choice;
- locking/transaction strategy.

Đó là input cho Dev Kit. Engineering Impact là capability/stage ngữ nghĩa bên trong Dev Kit, chịu trách nhiệm WHERE / WHO OWNS trước khi technical planning quyết định HOW.

## Nguồn nền tảng

Claim level và reference standards/frameworks nằm ở [FOUNDATIONS.md](FOUNDATIONS.md). Exact upstream revision/license nằm ở [PROVENANCE.md](PROVENANCE.md).

---

English: [Architecture](../en/ARCHITECTURE.md)
