# Cài đặt

Clone repository, sau đó chạy installer khi shell đang ở project muốn dùng BA Kit. Project scope phù hợp nhất khi mỗi project cần bộ skill riêng.

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

## Target được hỗ trợ

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

Installer giữ nguyên skill cùng tên đã tồn tại; không merge/overwrite. Reinstall idempotent. Uninstall chỉ xóa skill do BA Kit quản lý nếu nội dung chưa bị sửa.

## Doctor kiểm tra gì?

Doctor kiểm tra:

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

### Quan trọng: READY không đồng nghĩa mọi tool runtime đã cài

Doctor hiện **không phải dependency manager cho external tooling** và không chứng minh runtime acceptance.

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

---

English: [Installation](../en/INSTALLATION.md)
