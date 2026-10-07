# Cài đặt

Chọn đúng committed revision được review hoặc release evidence tương ứng cho phép. Với Internal/Pilot RC hoặc release sau này, dùng tag chính xác hoặc SHA được evidence bind. Chỉ dùng `main` khi chủ động chọn `main` để phát triển. Ghi lại SHA của checkout và cài đặt từ chính checkout đó; không dùng working branch tạm thời làm nguồn release. Xem [trạng thái phát hành](RELEASE.md).

~~~powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\tools\agent-skills
git checkout "<approved-ref>"
git rev-parse HEAD
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd ~/src/agent-skills
git checkout "<approved-ref>"
git rev-parse HEAD
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Thay `<approved-ref>` bằng tag hoặc commit SHA chính xác đã được cho phép. Lưu SHA được in ra cùng installation evidence và dùng checkout này cho cả installer lẫn Doctor. Khi phát triển từ `main`, hãy chủ động chọn `main` và ghi SHA đã resolve theo cùng cách.

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

## Cài Test Kit VNext: Manual, Automation và Execution

Test Kit VNext gồm Manual, Automation và Execution; package cần Python 3.10+ và Codex CLI. Với Codex project scope, installer bootstrap starter `_bmad/tea/config.yaml` khi file chưa có và giữ nguyên project config hiện hữu. Chạy trong project muốn tạo testware:

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

`_bmad/tea/config.yaml` là project-owned runtime config: installer chỉ tạo khi thiếu, Doctor kiểm tra các field TEA bắt buộc, và uninstall không xóa file này. Starter dùng path tương đối (`test-runs`) để có thể commit cùng repository. Với project dùng Git, nên review và commit config này để tránh drift giữa các tester.\n\nBA Kit có thể cài trước hoặc sau Test Kit bằng lệnh `ba` phía trên. Cả hai dùng `.agents/skills/` nhưng ownership tách biệt. Test Kit cài `test-kit`, `bmad-testarch-test-design`, `create-test-cases`; runtime, pin, license, root definition và package authority nằm dưới `.agents/skills/.test-kit/`. Cài Test không tự cài npm/pip package qua mạng.

`TEST_KIT_CODEX_COMMAND` là command/path override của Codex CLI. Nếu không đặt, resolver tìm Codex trên `PATH`. Override sai là lỗi rõ ràng, không fallback sang cài đặt riêng của máy. Windows npm shim `.cmd`/`.ps1` được resolver xử lý bằng argv rời, không nối shell command string.

## Project Foundation opt-in

Project Foundation là capability Shared SDLC riêng, chưa phải Kit thứ tư. Cài
Shared runtime và skill vào một install home tường minh:

~~~powershell
python C:\tools\agent-skills\tooling\install_dev_kit.py --source-root C:\tools\agent-skills --install-home C:\agent-runtime
python C:\agent-runtime\runtime\v1\project-foundation\scripts\project_foundation.py inventory --project-root C:\path\to\your-project
~~~

Để đưa skill vào profile Codex tách biệt, tạo profile mới với
`python tooling/prepare_agent_profile.py --destination <fresh-profile> --foundation`.
Profile và Dev runtime mang theo cùng deterministic Shared payload. Xem
[Project Foundation workflow](../project-foundation.md) để biết các mode,
producer commands và Human Gate. CLI dừng ở review; approval vẫn thuộc trusted host.

### Doctor và drift của Test Kit

Doctor Test đọc package manifest/authority và install record đã cài; kiểm tra managed-file hashes, import closure của Test/BA/Dev/Shared SDLC, pinned skills, schemas/templates/examples và TEA project config. `READY` nghĩa package/core capability sẵn sàng; Doctor không đánh giá BA approval, `APPROVED_DESIGN`, `APPROVED_TESTWARE`, execution hay verification. Thiếu optional XMind/Excel dependency cho `DEGRADED`; lỗi integrity hoặc capability bắt buộc cho `FAIL`. Ví dụ:

| Finding | Hành động |
|---|---|
| `PACKAGE_DEFINITION_INVALID`, `PACKAGE_AUTHORITY_INVALID`, `PACKAGE_METADATA_INVALID` | Kiểm tra package gốc; cài lại từ cùng revision đã pin. Không tự sửa digest để làm Doctor xanh. |
| `MODIFIED_MANAGED_FILE` | Kiểm tra local edit; reinstall giữ edit và Doctor còn báo drift cho đến khi khôi phục đúng bytes. |
| `MISSING_MANAGED_FILE` | Khôi phục từ cùng package version, chạy Doctor lại. |
| `DEPENDENCY_MISSING` | Cài dependency chỉ khi cần projection; trạng thái `DEGRADED` không chặn core VNext. |

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
- V1/VNext workflow-state và source-authority contracts;
- engineering-handoff contract;
- `ba_vnext.py`, `ba_contracts.py`, validators và VNext templates đã cài;
- isolated import Shared SDLC payload từ skill đã cài;
- canonical SRS contract và atomic BA skill bắt buộc.

| Status | Ý nghĩa |
|---|---|
| **READY** | Required skills/contracts đạt và optional skills có sẵn |
| **DEGRADED** | Required skills/contracts đạt nhưng thiếu optional skill |
| **FAIL** | Required skill/contract lỗi |

FAIL exit 1; READY/DEGRADED exit 0.

### Quan trọng với BA Kit: READY không đồng nghĩa mọi tool runtime đã cài

Doctor BA Kit **không phải dependency manager cho external tooling**, và không chứng minh Human approval, baseline đã approved, feature readiness hay full runtime acceptance. READY chỉ xác nhận package capability closure. Doctor Test Kit có thêm kiểm tra package integrity và dependency được khai báo; nó cũng không tự cài dependency.

Ví dụ một installation có thể READY nhưng vẫn thiếu tool để export Word/PNG/browser.

Maintainer acceptance cho Test gồm cài vào project sạch, chạy Doctor, hoàn tất hai Human Gate qua runtime cô lập, xác nhận lại Approved Testware manifest và chạy acceptance từ kits/test/acceptance.yaml. Xem trang release.

## Runtime prerequisite theo capability

### Core BA workflow

Cần:

- Python 3.10+ là baseline được hỗ trợ cho BA/Test;
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

## Bản đồ cài suite và policy Windows

Mỗi capability có cách cài riêng; suite không có một lệnh cài tất cả Kit.

| Capability | Cài đặt | Xác minh |
|---|---|---|
| BA | tooling/install.ps1 ba --agent codex --scope project (hoặc install.sh) | tooling/doctor.ps1 ba --agent codex --scope project |
| Dev VNext và Shared runtime | python -I tooling/install_dev_kit.py --source-root <checkout> --install-home <install-home> | Thêm <install-home>/bin vào PATH; chạy `devkit doctor` |
| Test Manual + Automation + Execution | tooling/install.ps1 test --agent codex --scope project (hoặc install.sh) | tooling/doctor.ps1 test --agent codex --scope project |
| Project Foundation | Shared runtime ở trên; theo [Foundation guide](PROJECT_FOUNDATION.md) | Chạy Foundation doctor qua workflow/host đã cài |

BA và Test dùng Python 3.10+ làm baseline hỗ trợ trong tài liệu. Dev installer dùng Python đã chọn để tạo runtime cách ly. Để cấu hình full toolkit ít bất ngờ nhất, dùng Python 3.10+ trừ khi candidate Dev được chọn yêu cầu bản mới hơn. Luôn dùng committed framework checkout đúng revision.

Windows checkout mặc định được hỗ trợ nhờ .gitattributes giữ package-source bytes ổn định. core.autocrlf=false không phải prerequisite. Không sửa hash package authority bằng tay.

## Nâng cấp và xác minh version

Đọc [suite manifest](../../tooling/sdlc-suite.json) và manifest từng Kit trước khi nâng cấp. Ghi commit bằng git rev-parse HEAD, chạy installer của Kit từ revision đã chọn rồi chạy Doctor. Reinstall giữ managed file đã sửa và báo drift; review local edit trước khi khôi phục managed file. Xem [Troubleshooting](TROUBLESHOOTING.md) để xử lý mismatch an toàn.
