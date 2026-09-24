# Cài đặt

Clone repository của Kit, sau đó chạy installer khi shell đang ở dự án bạn muốn dùng BA Kit. Project scope dùng thư mục làm việc hiện tại để cài riêng cho dự án. Sau khi cài, chạy **Doctor** (lệnh kiểm tra trạng thái cài đặt).

~~~powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Thay đường dẫn ví dụ của repository và dự án bằng đường dẫn thực tế.

## Các target được hỗ trợ

Dùng wrapper PowerShell hoặc shell tương ứng trong **tooling/**. Các tham số dưới đây dùng giống nhau cho **install**, **doctor** và **uninstall**.

| Target | Tham số |
|---|---|
| Codex project | **ba --agent codex --scope project** |
| Codex user | **ba --agent codex --scope user** |
| Claude Code project | **ba --agent claude-code --scope project** |
| Claude Code user | **ba --agent claude-code --scope user** |
| Thư mục generic | **ba --agent generic --target PATH** |

Ví dụ từ thư mục dự án trên PowerShell:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope user
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent claude-code --scope project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent generic --target C:\path\to\agent\skills
~~~

Ví dụ từ thư mục dự án trên Bash:

~~~bash
~/src/agent-skills/tooling/install.sh ba --agent codex --scope user
~/src/agent-skills/tooling/install.sh ba --agent claude-code --scope project
~/src/agent-skills/tooling/install.sh ba --agent generic --target /path/to/agent/skills
~~~

Để chạy Doctor hoặc gỡ cài đặt, gọi wrapper **doctor.ps1** / **doctor.sh** hoặc **uninstall.ps1** / **uninstall.sh** tương ứng với cùng tham số kit và target. Ví dụ:

~~~powershell
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent claude-code --scope project
& 'C:\tools\agent-skills\tooling\uninstall.ps1' ba --agent generic --target C:\path\to\agent\skills
~~~

~~~bash
~/src/agent-skills/tooling/doctor.sh ba --agent claude-code --scope project
~/src/agent-skills/tooling/uninstall.sh ba --agent generic --target /path/to/agent/skills
~~~

Skill Codex project được cài tại **.agents/skills**; Claude Code project dùng **.claude/skills**. User scope cài vào thư mục tương ứng trong home folder. Project scope phù hợp khi chỉ muốn dùng BA Kit cho một dự án. Generic bắt buộc có **--target**. Tham số này cũng có thể ghi đè đường dẫn agent native để kiểm tra cô lập.

Các kiểm tra cấu trúc đã đạt gồm Codex project install, cài lặp idempotent, Doctor, gỡ cài đặt an toàn và cô lập dự án. Generic PowerShell/Bash và cấu trúc cài đặt Claude Code cũng đã được kiểm tra; runtime Claude chưa được chạy. Xem [Trạng thái phát hành](RELEASE.md).

## Trạng thái Doctor

Doctor kiểm tra skill bắt buộc/tùy chọn đã cài, manifest của kit, hợp đồng workflow-state/source-authority và hợp đồng handoff.

| Trạng thái | Ý nghĩa |
|---|---|
| **READY** | Skill bắt buộc, hợp đồng và các skill tùy chọn đều đạt/có sẵn. |
| **DEGRADED** | Skill bắt buộc và hợp đồng đạt, nhưng thiếu một hoặc nhiều skill tùy chọn. |
| **FAIL** | Thiếu hoặc sai skill bắt buộc, hoặc hợp đồng bắt buộc không đạt. |

**FAIL** trả mã thoát 1. **READY** và **DEGRADED** trả mã thoát 0. Doctor không chạy một phiên BA và không chứng minh runtime acceptance.

## Yêu cầu và an toàn

- Cần Python 3.8 trở lên. PowerShell tìm **python** trên PATH. Bash dùng **python3** hoặc executable được chỉ định trong biến môi trường **PYTHON**.
- Không cần package Python, Skills Manager, agent profile hay thay đổi cấu hình agent toàn cục.
- Thành phần được lấy từ [kit.yaml](../../kits/ba/kit.yaml). Installer giữ nguyên skill cùng tên đã có; không merge hay ghi đè.
- Cài lặp lại an toàn. Gỡ cài đặt chỉ xóa skill BA Kit không bị sửa; skill đã sửa hoặc dùng chung được giữ lại.

Xem [Hướng dẫn nhanh](BA_KIT_QUICKSTART.md) để bắt đầu.

---

English: [Installation](../en/INSTALLATION.md)
