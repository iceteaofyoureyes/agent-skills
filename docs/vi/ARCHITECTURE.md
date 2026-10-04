# Tổng quan kiến trúc

## Mục tiêu

BA Kit tổ chức atomic skills cho business analysis; Test Kit V1 tổ chức native test analysis và manual testware. Human vẫn sở hữu business decision và từng approval gate.

~~~text
BA Kit = WHAT
Engineering Impact = WHERE / WHO OWNS
Dev Kit + repo-local Spec Kit = HOW (planned)
Test Kit V1 + TEA/Katalon = HOW DO WE PROVE IT
~~~

## Layer

Các integration contract hiện nằm trong `shared/sdlc`; compatibility adapter giữ
nguyên import path và semantics BA/Test/Dev. Xem
[Shared SDLC Core Wave 1](../en/SHARED_SDLC_CORE_WAVE1.md) mô tả source owner và
runtime payload theo kit. Project Foundation tích hợp producer observations, exact
review refs, Knowledge Impact và clean installed runtime theo cùng Shared authority.

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

Atomic skills được lưu canonical ở repository root. **kits/ba/kit.yaml** là nguồn duy nhất cho BA Kit composition.

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

Test Kit nhận **Approved BA Baseline** trực tiếp. TEA là analysis/advisory; Canonical Test Design được Human duyệt là coverage authority; Canonical Testcases được Human duyệt là manual testware authority. XMind/Excel là derived projections, không reverse import. P0–P3 là priority tư vấn, không có quyền thay BA rule hoặc Human Gate.

## Project modes

- brownfield;
- greenfield;
- document-only;
- visual-assisted.

Workflow không bắt mọi request chạy full pipeline; nó bắt đầu từ earliest safe checkpoint.

## Responsibility flow

| Stage | Question | Status |
|---|---|---|
| BA Kit | **WHAT**? | VNext packaging candidate; cần Tier 3 fresh-install acceptance; chưa stable release |
| Engineering Impact | **WHERE / WHO OWNS**? | Planned |
| Dev Kit + Spec Kit | **HOW**? | Planned |
| Test Kit V1 | **HOW DO WE PROVE IT**? | Core, XMind, Excel, Packaging V1 Human accepted; package đã commit |

~~~text
Requirement → BA Kit → Approved BA Baseline
                         ├──→ Engineering Impact → Dev/Spec path (planned)
                         └──→ Test Kit V1 → Canonical Test Design
                                        → Human Design Gate
                                        → Canonical Testcases
                                        → Human Case Gate
                                        → APPROVED_TESTWARE → STOP_V1
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

Đó là input cho Engineering Impact.

Test Kit không đòi output của Dev Kit để bắt đầu: approved BA handoff và hashed sources là đủ cho Test Design. Nếu testcase cần API/UI/setup/observation contract chưa duyệt, nó khai báo execution dependency; material `OPEN` chặn Case Gate approval. Xem [Test Kit workflow](TEST_KIT_WORKFLOW.md).

## Nguồn nền tảng

Claim level và reference standards/frameworks nằm ở [FOUNDATIONS.md](FOUNDATIONS.md). Exact upstream revision/license nằm ở [PROVENANCE.md](PROVENANCE.md).

---

English: [Architecture](../en/ARCHITECTURE.md)
