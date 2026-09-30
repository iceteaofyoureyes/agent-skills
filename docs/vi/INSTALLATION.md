# Cài đặt

Clone repository, sau đó chạy installer khi shell đang ở project muốn dùng Kit. BA và Test cài độc lập hoặc cùng project; mỗi Kit có install record và managed paths riêng. Test Kit V1 chỉ hỗ trợ Codex **project scope**.

~~~powershell
git clone --branch main https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone --branch main https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

## Target BA Kit được hỗ trợ

| Target | Arguments |
|---|---|
| Codex project | **ba --agent codex --scope project** |
| Codex user | **ba --agent codex --scope user** |
| Claude Code project | **ba --agent claude-code --scope project** |
| Claude Code user | **ba --agent claude-code --scope user** |
| Generic directory | **ba --agent generic --target PATH** |

PowerShell:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope user
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent claude-code --scope project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent generic --target C:\path\to\agent\skills
~~~

Bash:

~~~bash
~/src/agent-skills/tooling/install.sh ba --agent codex --scope user
~/src/agent-skills/tooling/install.sh ba --agent claude-code --scope project
~/src/agent-skills/tooling/install.sh ba --agent generic --target /path/to/agent/skills
~~~

Gỡ cài đặt hoặc Doctor dùng cùng kit/target arguments với **uninstall.ps1/.sh** và **doctor.ps1/.sh**.

## Vị trí cài

- Codex project: **.agents/skills**
- Claude Code project: **.claude/skills**
- user scope: agent-native skills directory trong home
- generic: bắt buộc chỉ rõ **--target**

Installer giữ nguyên file/skill người dùng đã sửa; không merge/overwrite. Reinstall idempotent. Uninstall chỉ xóa managed asset chưa bị sửa và thuộc Kit đang gỡ.

## Cài Test Kit V1

Test Kit V1 cần Python 3.10+, Codex CLI và project `_bmad/tea/config.yaml` phù hợp với skill TEA đã pin. Chạy trong project muốn tạo testware:

~~~powershell
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
~~~

~~~bash
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh test --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh test --agent codex --scope project
~~~

BA Kit có thể cài trước hoặc sau Test Kit bằng lệnh `ba` phía trên. Cả hai dùng `.agents/skills/` nhưng ownership tách biệt. Test Kit cài `test-kit`, `bmad-testarch-test-design`, `create-test-cases`; runtime, pin, license, root definition và package authority nằm dưới `.agents/skills/.test-kit/`. Cài Test không tự cài npm/pip package qua mạng.

`TEST_KIT_CODEX_COMMAND` là command/path override của Codex CLI. Nếu không đặt, resolver tìm Codex trên `PATH`. Override sai là lỗi rõ ràng, không fallback sang cài đặt riêng của máy. Windows npm shim `.cmd`/`.ps1` được resolver xử lý bằng argv rời, không nối shell command string.

### Doctor và drift của Test Kit

Doctor Test đọc đúng `.agents/skills/.test-kit/kit.yaml` đã cài, kiểm tra pin authority, payload, install record, từng managed file và dependency bắt buộc. `READY` nghĩa các hợp đồng bắt buộc đạt; dependency XMind/Excel tùy chọn có thể được báo `DEPENDENCY_MISSING` nhưng core vẫn hoạt động. `FAIL` nghĩa không được coi package là healthy. Ví dụ:

| Finding | Hành động |
|---|---|
| `PACKAGE_DEFINITION_INVALID`, `PACKAGE_AUTHORITY_INVALID`, `PACKAGE_METADATA_INVALID` | Kiểm tra package gốc; cài lại từ cùng revision đã pin. Không tự sửa digest để làm Doctor xanh. |
| `MODIFIED_MANAGED_FILE` | Kiểm tra local edit; reinstall giữ edit và Doctor còn báo drift cho đến khi khôi phục đúng bytes. |
| `MISSING_MANAGED_FILE` | Khôi phục từ cùng package version, chạy Doctor lại. |
| `DEPENDENCY_MISSING` | Phân biệt Codex bắt buộc với XMind/Excel tùy chọn; cài dependency của capability cần dùng. |

Reinstall và uninstall Test Kit dùng cùng scope:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\tools\agent-skills\tooling\uninstall.ps1' test --agent codex --scope project
~~~

Uninstall Test giữ BA Kit và file không thuộc Test; file Test do Human sửa được giữ lại theo safety policy.

### Optional XMind và Excel

Core Test Design/Testcase không phụ thuộc XMind/Excel. Chỉ bootstrap sau khi quyết định dùng projection:

~~~powershell
Push-Location .agents/skills/.test-kit/tooling/xmind
npm ci
Pop-Location
python -m pip install --require-hashes -r .agents/skills/.test-kit/tooling/requirements-excel.lock
~~~

XMind cần Node.js 18+/npm 9+ và lockfile đã pin. Excel dùng `openpyxl==3.1.5`/`et-xmlfile==2.0.0` từ hash-locked file trong Python environment chạy exporter. Đây là hai bước **tùy chọn, tường minh**; không cần chạy cả hai. [Test Kit Quick Start](TEST_KIT_QUICKSTART.md) mô tả workflow sau cài.

## Doctor kiểm tra gì?

Doctor BA Kit kiểm tra:

- manifest/composition;
- required/optional skill directories;
- Agent Skills frontmatter;
- workflow-state/source-authority contracts;
- engineering-handoff contract.

| Status | Ý nghĩa |
|---|---|
| **READY** | Required skills/contracts đạt và optional skills có sẵn |
| **DEGRADED** | Required skills/contracts đạt nhưng thiếu optional skill |
| **FAIL** | Required skill/contract lỗi |

FAIL exit 1; READY/DEGRADED exit 0.

### Quan trọng với BA Kit: READY không đồng nghĩa mọi tool runtime đã cài

Doctor BA Kit **không phải dependency manager cho external tooling** và không chứng minh runtime acceptance. Doctor Test Kit có thêm kiểm tra package integrity và dependency được khai báo; nó cũng không tự cài dependency.

Ví dụ một installation có thể READY nhưng vẫn thiếu tool để export Word/PNG/browser.

## Runtime prerequisite theo capability

### Core BA workflow

Cần:

- Python 3.8+ cho installer/validators;
- agent runtime có quyền đọc project/artifact cần review.

Installer không yêu cầu Skills Manager, agent profile hay global config change.

### DOCX / Word template

**document-docx** chọn tool theo task.

Các action thường có thể cần:

- **python-docx** cho structural create/edit;
- **docxtpl** cho Word-authored template có placeholder;
- LibreOffice hoặc Microsoft Word cho render/PDF/fidelity check tùy workflow.

BA Kit installer **không tự pip-install** các package này.

Trước khi hứa một DOCX feature, agent phải kiểm tra tool/library version theo document-docx skill.

Xem [SRS và DOCX](SRS_DOCX_GUIDE.md).

### Draw.io

Core .drawio authoring/validation có nhiều path chỉ cần Python.

Để native export PNG/SVG/PDF cần **draw.io/diagrams.net desktop CLI** khả dụng.

Graphviz là optional cho một số auto-layout workflow.

Nếu binary export không có, agent có thể vẫn tạo/edit source .drawio theo capability phù hợp nhưng phải báo limitation thay vì claim export đã thực hiện.

Xem [Draw.io, visual input và prototype](DIAGRAMS_PROTOTYPES.md).

### Prototype / browser check — optional

Optional browser workflow có thể cần:

- Node.js/npm/npx;
- Playwright CLI/browser runtime;
- project frontend dependencies.

Các dependency này không được BA Kit installer tự cài.

### Figma

BA Kit **không bundle Figma connector**.

Direct Figma access cần connector/integration ngoài Kit + Human authorization. Nếu không có, dùng screenshot/PDF/image/HTML/local export.

## Kiểm tra sau cài

Sau Doctor READY/DEGRADED, nên test đúng capability mình định dùng.

### Core BA

~~~text
Mở agent trong project và yêu cầu:
Review requirement này. REVIEW only.
~~~

### DOCX

Trước khi tạo template output, kiểm tra Python/package/tool theo document-docx workflow.

### Draw.io

Nếu cần export:

~~~text
drawio --version
~~~

hoặc dùng doctor/probe riêng của drawio-skill khi phù hợp.

### Prototype

Kiểm tra project frontend + npx/Playwright trước khi yêu cầu render.

## Các kiểm tra package đã có

Đã có structural evidence cho:

- Codex project install;
- idempotent reinstall;
- Doctor;
- safe uninstall;
- project isolation;
- generic PowerShell/Bash;
- Claude Code structural install.

Đây là package evidence, không phải full runtime BA acceptance. Xem [Release status](RELEASE.md).

## Xem thêm

- [Quick Start](BA_KIT_QUICKSTART.md)
- [Capabilities](BA_KIT_CAPABILITIES.md)
- [SRS/DOCX](SRS_DOCX_GUIDE.md)
- [Draw.io/Visual/Prototype](DIAGRAMS_PROTOTYPES.md)
- [Test Kit Quick Start](TEST_KIT_QUICKSTART.md)
- [Test Kit capabilities](TEST_KIT_CAPABILITIES.md)

---

English: [Installation](../en/INSTALLATION.md)
