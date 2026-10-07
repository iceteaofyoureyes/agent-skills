# Bắt đầu với Agent-Assisted SDLC Toolkit

Trang này dành cho người muốn **dùng Kit** mà chưa cần đọc schema hay contract nội bộ.

## 1. Chọn thứ anh/chị thực sự cần

Không cần cài cả ba Kit.

| Nhu cầu | Bắt đầu với |
|---|---|
| "Tôi có requirement và cần làm rõ WHAT." | **BA Kit** |
| "Tôi đã có requirement được duyệt và cần triển khai." | **Dev Kit** |
| "Tôi cần Test Design / Testcases / automation / execution." | **Test Kit** |
| "Project mới hoặc project cũ thiếu tài liệu/kiến trúc đáng tin." | **Project Foundation** |
| "Tôi muốn chạy full lifecycle." | Foundation khi cần → BA → Dev → Test |

Xem [Kit catalog](../../kits/README.md).

## 2. Prerequisite dễ nhớ

Luôn cài từ một committed revision chính xác.

| Yêu cầu | Hướng dẫn hiện tại |
|---|---|
| Git | Bắt buộc |
| Python | **3.10+** là baseline tài liệu cho BA/Test; dùng 3.10+ để cấu hình full toolkit ít bất ngờ nhất |
| OS | Workflow hỗ trợ Windows và Linux |
| Codex | Đường end-to-end được verify chính |
| Claude Code | BA có installation target khi tài liệu ghi rõ; không mặc định toàn bộ cross-Kit flow đã được verify trên Claude Code |
| Spec Kit | Cần cho Dev/public conformance hiện tại; version release-gate chính xác nằm trong conformance guide |
| XMind / Excel | Projection tùy chọn của Test |

Chi tiết từng capability: [Cài đặt](INSTALLATION.md).

## 3. Chọn exact source revision

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git
cd agent-skills
git checkout "<approved-ref>"
git rev-parse HEAD
~~~

Lưu SHA đã resolve cùng evidence cài đặt/review.

## 4. Chỉ cài Kit cần dùng

### BA Kit

~~~powershell
& 'C:\path\to\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\path\to\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

### Test Kit

~~~powershell
& 'C:\path\to\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\path\to\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
~~~

### Dev Kit / shared runtime

~~~powershell
python -I C:\path\to\agent-skills\tooling\install_dev_kit.py --source-root C:\path\to\agent-skills --install-home C:\agent-runtime
~~~

Sau đó dùng Dev runtime/Doctor theo [Cài đặt](INSTALLATION.md) và [Dev Kit README](../../kits/dev/README.md).

Doctor chỉ chứng minh package/capability sẵn sàng. Doctor không phải Human approval và không phải product verification.

## 5. Cho agent một task đầu tiên có boundary rõ

Đây là prompt định hướng, không phải command đặc biệt.

### BA

> Review requirement này ở REVIEW mode. Tìm ambiguity, business rule còn thiếu và câu hỏi cần Human trả lời. Không tự approve và dừng trước Human Gate.

### Developer

> Bắt đầu FEATURE_DELIVERY từ Engineering Handoff đã được duyệt. Phân tích repository và technical impact. Không tự đoán WHAT còn thiếu; dừng ở UPSTREAM_GAP hoặc Human technical gate nếu có.

### Tester

> Tạo Test Design từ authority input đã được duyệt. Giữ trace BR/FR và dừng tại Human Design Gate.

Workflow của Kit quyết định transition hợp lệ; prompt không thay thế authority bắt buộc.

## 6. Brownfield hay greenfield?

### Project đang chạy / brownfield

Dùng Project Foundation khi context hệ thống hiện tại không đủ đáng tin. Recovery workflow tách CURRENT_SYSTEM, CONFIRMED, INFERRED và UNKNOWN thay vì coi code hiện tại là target mong muốn.

Xem [Project Foundation](PROJECT_FOUNDATION.md).

### Project mới / greenfield

Dùng Foundation khi cần target architecture/project context được review. Business behavior vẫn do BA/Human sở hữu; Foundation không approve requirement.

## 7. Quy tắc cần nhớ

~~~text
BA          → WHAT
Engineering → WHERE / WHO OWNS / HOW
Test        → chứng minh behavior đã được duyệt
Human       → semantic authority cuối cùng
~~~

Dev gặp WHAT chưa rõ thì route upstream. Test gặp spec gap thì classify và route; không tự phát minh expected behavior.

## 8. Xem một ví dụ đầy đủ

Đọc [Ví dụ full flow](FULL_FLOW_EXAMPLE.md). Ví dụ có cả hai nhánh:

- initial PASS sạch → VERIFIED;
- DEFECT → Dev Fix → READY_FOR_RETEST → retest → VERIFIED / REOPENED.

## Đọc tiếp

- [FAQ](FAQ.md)
- [Kiến trúc](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Release status](RELEASE.md)
