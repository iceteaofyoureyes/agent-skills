# Nền tảng thiết kế, chuẩn tham chiếu và design lineage

Tài liệu này giải thích **vì sao kiến trúc và workflow của Agent Skills / BA Kit được thiết kế như hiện tại**, các chuẩn/framework/community project nào được dùng làm tham chiếu, và mức độ mà repository thực sự áp dụng chúng.

Tài liệu này khác với [Nguồn gốc và giấy phép](PROVENANCE.md):

- **PROVENANCE.md** trả lời: một skill/file cụ thể đến từ đâu, revision nào và license gì.
- **FOUNDATIONS.md** trả lời: một quyết định kiến trúc hoặc workflow dựa trên chuẩn, practice hoặc nguồn tham khảo nào.

Mục tiêu là tạo design lineage có thể kiểm chứng, không mượn uy tín bằng cách gắn tên một standard/framework mà không có mapping cụ thể.

> Snapshot tham chiếu: **2026-09-24**. Các nguồn bên ngoài có thể tiếp tục thay đổi; các claim dưới đây chỉ áp dụng cho trạng thái được kiểm chứng tại thời điểm này.

## Chính sách mức claim

| Mức | Nghĩa trong repository này |
|---|---|
| **ADOPTED** | Repository chủ động triển khai một format/contract bên ngoài ở phạm vi được nêu rõ. |
| **ALIGNED** | Một số nguyên tắc/practice được mapping rõ, nhưng repository **không** claim certification hay full conformance. |
| **UPSTREAM CAPABILITY SOURCE** | Code/skill thực sự được lấy hoặc sửa từ upstream; revision/license chính xác nằm trong PROVENANCE.md. |
| **DESIGN INFLUENCE** | Ý tưởng/phương pháp được tham khảo nhưng không tạo dependency hay claim tương thích đầy đủ. |
| **PLANNED INTEGRATION** | Được chọn cho phase downstream nhưng chưa phải capability đã triển khai/chấp nhận trong BA Kit RC1. |
| **INTERNAL DESIGN** | Quyết định riêng của project, phải được chứng minh bằng contract, test, benchmark và Human review của chính repository. |

Repository **không** claim:

- ISO/IEC/IEEE 29148 certification hoặc full conformance;
- IIBA/BABOK certification hoặc full methodology compliance;
- BA Kit là fork/implementation của GitHub Spec Kit hay BMad Method;
- Test Kit/TEA đã được triển khai trong BA Kit RC1;
- các tổ chức/upstream được nêu trong tài liệu endorse repository này.

## Ma trận nền tảng

| Nguồn | Mức claim | Phần repository liên quan | Điều được kế thừa / tham chiếu | Điều vẫn là thiết kế riêng |
|---|---|---|---|---|
| [Agent Skills](https://agentskills.io/) | **ADOPTED** | Atomic skill packaging | Skill là folder có `SKILL.md`; metadata + instructions; có thể kèm scripts/references/assets; progressive disclosure | `kit.yaml`, BA/Dev/Test Kit model, installer, Doctor, Human Gate và handoff contracts |
| [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) | **ALIGNED** | Requirements/SRS discipline | Requirements engineering xuyên vòng đời, well-formed requirements, requirements information items/SRS, requirements management | Nhãn evidence, BA semantic authority, WHAT/WHERE/HOW split và artifact schema cụ thể |
| [IIBA BABOK / Requirements Life Cycle Management](https://www.iiba.org/knowledgehub/business-analysis-body-of-knowledge-babok-guide/5-requirements-life-cycle-management/5-1-trace-requirements/) | **ALIGNED** | Traceability và Human approval | Trace, maintain, assess changes, approve requirements; specify/model, verify, validate requirements | Human Gate state machine, immutable handoff revision/hash policy và agent routing |
| [45ck/business-analysis-skills](https://github.com/45ck/business-analysis-skills) | **UPSTREAM CAPABILITY SOURCE** | Một số BA atomic skills | Gap audit, interrogation, quality check, business rule extraction | BA workflow orchestration, semantic authority, Human Gates và SRS replacement project-owned |
| [DiUS/agent-toolkit](https://github.com/DiUS/agent-toolkit) | **UPSTREAM CAPABILITY SOURCE** | `codebase-discovery` | Brownfield/current-code discovery capability | Cách BA Kit phân loại CURRENT_SYSTEM và ngăn current behavior tự trở thành target requirement |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | **PLANNED INTEGRATION** | Dev Kit downstream | Spec-driven development: specification → plan → tasks → implementation/convergence; tách “what/why” trước “how” | Engineering Impact chạy trước Spec Kit; central BA truth; Spec Kit per affected repo |
| [BMad Method](https://docs.bmad-method.org/) | **DESIGN INFLUENCE** | Cross-session/project workflow thinking | Human giữ quyền quyết định; existing-codebase-first; context/decision được duy trì có chủ đích | 3-Kit product model, BA semantic authority, Impact contract và installer architecture |
| [BMad Test Architect (TEA)](https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise) | **PLANNED INTEGRATION / DESIGN INFLUENCE** | Test Kit downstream | Risk-based test design, traceability, quality/release gates; stack-neutral verification core tách khỏi execution target | BA→Test direct business trace, enterprise manual-test-first workflow và final Test Kit composition |

## 1. Agent Skills — format được ADOPT

[Agent Skills specification](https://agentskills.io/specification) định nghĩa skill tối thiểu là một thư mục có `SKILL.md` chứa YAML frontmatter và Markdown instructions; `scripts/`, `references/` và `assets/` là các resource tùy chọn. Specification cũng mô tả progressive disclosure: metadata được discover trước, instructions được load khi skill được activate và resource chi tiết chỉ load khi cần.

Repository áp dụng trực tiếp model này cho atomic skills:

~~~text
<skill-name>/
├── SKILL.md
├── references/   # khi cần
├── scripts/      # khi cần
├── assets/       # khi cần
└── LICENSE       # khi cần cho redistribution
~~~

Điểm **không thuộc Agent Skills standard** và do project tự thiết kế:

- role Kit (`ba`, sau này `dev`, `test`);
- `kits/<id>/kit.yaml`;
- installer/Doctor/uninstall;
- workflow-state;
- Human Gate semantics;
- Engineering Handoff;
- semantic authority của BA.

Vì vậy claim đúng là **“atomic skills follow/adopt the Agent Skills format”**, không phải “toàn bộ framework là Agent Skills standard”.

## 2. ISO/IEC/IEEE 29148 — alignment cho Requirements/SRS

ISO hiện liệt kê **ISO/IEC/IEEE 29148:2018, Edition 2** là bản International Standard được published; bản này được review và confirmed năm 2024. Tại snapshot 2026-09-24, **Edition 3 đang ở Draft International Standard (DIS)** và dự kiến thay thế bản 2018, nên repository chưa dùng draft làm normative baseline.

Các điểm BA Kit **aligned** với 29148 ở mức principle:

- requirements được quản lý xuyên lifecycle thay vì chỉ sinh một tài liệu một lần;
- tách requirement/business meaning khỏi implementation design;
- ưu tiên requirement rõ ràng, có thể kiểm tra và có nguồn;
- SRS/information item được tạo từ baseline đã được làm rõ;
- thay đổi requirement cần được kiểm soát thay vì silently overwrite.

Các cơ chế sau là **internal guardrails**, không phải thuật ngữ do ISO 29148 định nghĩa:

~~~text
CONFIRMED
CURRENT_SYSTEM
INFERRED
PROPOSED
UNKNOWN
~~~

Tương tự, invariant **“Tiếp tục != Approve”**, Human Gate và BA→Engineering Handoff là contract riêng của repository.

Do chưa thực hiện conformance audit đầy đủ theo standard, repository chỉ dùng từ **ALIGNED**, không dùng “ISO compliant”, “ISO certified” hay “conformant to ISO/IEC/IEEE 29148”.

## 3. IIBA BABOK — alignment cho lifecycle, traceability và approval

IIBA công khai Requirements Life Cycle Management với các task như:

- Trace Requirements;
- Maintain Requirements;
- Prioritize Requirements;
- Assess Requirements Changes;
- Approve Requirements.

BABOK KnowledgeHub cũng tách Requirements Analysis and Design Definition thành các hoạt động như Specify and Model, Verify và Validate Requirements.

BA Kit mapping các practice này vào:

~~~text
Requirement
→ clarification / confirmed decisions
→ Business Rules
→ SRS
→ explicit Human approval
→ Engineering Handoff
~~~

và downstream trace mục tiêu:

~~~text
CR
→ BR / FR / AC
→ Test Case
→ Execution
→ Automation
→ Result
~~~

Tuy nhiên BA Kit không cố triển khai toàn bộ BABOK knowledge areas, techniques hay governance model. Claim đúng là **selected-practice alignment**, không phải “BABOK implementation”.

## 4. Community BA capability — code provenance khác design lineage

Một số atomic capability của BA Kit thực sự đến từ community repo, đặc biệt:

- [45ck/business-analysis-skills](https://github.com/45ck/business-analysis-skills): requirements gap auditor, interrogator, quality check và business rule extractor;
- [DiUS/agent-toolkit](https://github.com/DiUS/agent-toolkit): `codebase-discovery`.

Đây là **UPSTREAM CAPABILITY SOURCE**, không chỉ là “inspiration”. Exact source path, revision, local changes và license được giữ trong [PROVENANCE.md](PROVENANCE.md).

Ngược lại, `ba-workflow`, Kit contract, Human Gate model và implementation hiện tại của `srs-function-document` là project-owned. Không gán các phần này cho upstream nếu không có evidence.

## 5. GitHub Spec Kit — downstream HOW, không phải BA source of truth

GitHub Spec Kit mô tả Spec-Driven Development theo hướng **define what and why before deciding how**, rồi đi qua specification → plan → tasks → implement → converge.

Điểm này hỗ trợ ranh giới mà framework đang hướng tới:

~~~text
BA Kit
WHAT
  ↓
Engineering Impact
WHERE / WHO OWNS
  ↓
repo-local Spec Kit / Dev
HOW
~~~

Nhưng cần giữ đúng claim:

- Spec Kit **chưa được tích hợp** trong BA Kit RC1;
- Engineering Impact trước Spec Kit là quyết định của framework này, không phải claim rằng Spec Kit bắt buộc flow đó;
- BA business baseline không được biến thành repo-local implementation spec;
- dự kiến Spec Kit chạy **per affected implementation repo** sau khi Impact xác định phạm vi.

Do đó trạng thái hiện tại là **PLANNED INTEGRATION**.

## 6. BMad Method — design influence cho Human control và brownfield

BMad hiện nhấn mạnh việc Human “make the calls”, hỗ trợ existing codebases và dùng verified project context thay vì bắt agent tin vào documentation stale. Đây là các pattern phù hợp với các quyết định của framework:

- Human giữ approval/accountability;
- brownfield cần đọc current source trước;
- decision/context quan trọng phải durable;
- không ép mọi thay đổi đi qua cùng một lượng ceremony.

BA Kit không dùng runtime/workflow engine của BMad và không phải derivative implementation của BMad Method. Vì vậy mức claim là **DESIGN INFLUENCE**.

## 7. TEA — nền tảng dự kiến cho Test Kit

BMad Test Architect (TEA) hiện mô tả một verification architecture hai lớp:

1. **TEA Core** quyết định cần verify gì, độ sâu nào, evidence nào và evidence có đủ cho release hay không;
2. **Execution targets** chuyển các quyết định đó thành test runnable theo stack cụ thể.

TEA cũng có risk-based test design, traceability và release/quality gates. Các đặc điểm này phù hợp với target Test Kit:

~~~text
BA Approved Baseline
        +
Dev Technical Evidence
        ↓
TEA/Test Design
        ↓
Risk
        ↓
Manual Test Cases
        ↓
Human Tester Review
        ↓
Execution
        ↓
Automation / Regression
        ↓
Quality Evidence
~~~

Tuy nhiên Test Kit chưa được triển khai/freeze. TEA hiện chỉ là **PLANNED INTEGRATION / DESIGN INFLUENCE**, không phải capability của BA Kit RC1.

## 8. Các quyết định INTERNAL DESIGN phải tự chứng minh

Các quyết định sau không được “mượn” ISO, BABOK, Spec Kit hay BMad để hợp thức hóa:

- BA Kit / Dev Kit / Test Kit là 3 role products;
- Core Skills là shared layer chứ không phải Kit thứ tư;
- atomic skills nằm flat ở root;
- `kit.yaml` là canonical composition;
- `"Tiếp tục" != "Approve"`;
- evidence labels và semantic authority;
- Engineering Impact = WHERE / WHO OWNS;
- Impact chạy trước repo-local Spec Kit;
- business truth ở central BA baseline;
- Test trace trực tiếp về BA IDs;
- manual testing là first-class.

Các quyết định này phải được đánh giá bằng evidence của chính project: contract validation, benchmark, regression test, fresh-session acceptance và Human review.

## 9. Evidence hierarchy của repository

Uy tín của framework không dựa vào số star hay logo của upstream. Evidence được ưu tiên theo chuỗi:

~~~text
External standard / documented methodology
        ↓
Exact upstream provenance where code is reused
        ↓
Project-owned contracts and explicit boundaries
        ↓
Automated validation / Doctor / regression tests
        ↓
Benchmark and semantic comparison
        ↓
Fresh-session runtime acceptance
        ↓
Human approval
~~~

Trạng thái BA Kit RC1 hiện tại:

- package/installer/Doctor/isolation: đã có evidence;
- provenance/license của BA Kit payload: READY;
- offline BA/SRS contract tests: PASS;
- CR-001 documentation examples: illustrative/contract-valid, không phải runtime proof;
- runtime preflight và project-local skill discovery: PASS;
- full fresh-session CR-001 run đầu tiên: **BA_KIT_RC1_CHANGES_REQUIRED**;
- exact tested SHA của run đó không được report, vì vậy current HEAD chưa có final runtime acceptance.

Xem [Trạng thái phát hành](RELEASE.md) để tránh biến test/package evidence hoặc một failed/stale run thành claim functional acceptance.

## 10. Nguồn tham khảo chính

Các link dưới đây là nguồn upstream/official được kiểm tra khi viết tài liệu này:

1. **Agent Skills**
   - Overview: https://agentskills.io/
   - Specification: https://agentskills.io/specification
2. **ISO/IEC/IEEE 29148**
   - Published 2018 standard: https://www.iso.org/standard/72089.html
   - Edition 3 DIS đang phát triển: https://www.iso.org/standard/94091.html
3. **IIBA**
   - Requirements Life Cycle Management / Trace Requirements: https://www.iiba.org/knowledgehub/business-analysis-body-of-knowledge-babok-guide/5-requirements-life-cycle-management/5-1-trace-requirements/
   - Business Analysis Standard — Requirements and Designs Life Cycle Management: https://www.iiba.org/knowledgehub/the-business-analysis-standard/5-applying-business-analysis-tasks/5-3-business-analysis-knowledge-areas/requirements-and-designs-life-cycle-management/
4. **GitHub Spec Kit**
   - https://github.com/github/spec-kit
5. **BMad Method**
   - https://docs.bmad-method.org/
   - Existing codebases: https://docs.bmad-method.org/existing-codebases/start-in-an-existing-codebase/
6. **BMad Test Architect (TEA)**
   - https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise
   - Verification architecture: https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise/blob/main/docs/explanation/verification-architecture.md
7. **Upstream BA/discovery capability**
   - https://github.com/45ck/business-analysis-skills
   - https://github.com/DiUS/agent-toolkit

Tên sản phẩm, standard và trademark thuộc chủ sở hữu tương ứng. Việc tham chiếu không ngụ ý endorsement, certification hay affiliation.

---

English: [Design Foundations, Standards, and Lineage](../en/FOUNDATIONS.md)
