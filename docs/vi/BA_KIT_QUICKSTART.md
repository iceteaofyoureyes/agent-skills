# Hướng dẫn nhanh BA Kit

**BA Kit** (Bộ công cụ Phân tích nghiệp vụ có AI hỗ trợ) giúp BA khám phá hệ thống hiện tại, tìm khoảng trống yêu cầu, ghi nhận quyết định của Human, chuẩn bị **Business Rules** (Quy tắc nghiệp vụ) và **SRS** (Tài liệu yêu cầu phần mềm), rồi tạo **Engineering Handoff** (bàn giao cho kỹ thuật) sau khi được phê duyệt. BA Kit hỗ trợ BA; không thay thế quyền sở hữu nghiệp vụ, trao đổi với khách hàng hay phê duyệt của Human.

BA Kit chịu trách nhiệm **WHAT** — hệ thống cần làm gì. Kit không thiết kế API hay cơ sở dữ liệu, không chỉ định người sở hữu triển khai và không viết mã production. Xem [Tổng quan kiến trúc](ARCHITECTURE.md) và [Quy trình và Human Gate](BA_KIT_WORKFLOW.md).

## Cài cho một dự án

Clone repository, sau đó chạy script từ thư mục dự án nơi bạn muốn dùng BA Kit. Project scope cài vào thư mục hiện tại. Thay các đường dẫn ví dụ bằng đường dẫn trên máy bạn.

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

Project scope đặt skill trong thư mục **.agents/skills** của dự án đó, giúp BA Kit chỉ có hiệu lực ở dự án cần dùng. [Cài đặt](INSTALLATION.md) có thêm lệnh cho Codex user scope, Claude Code, generic target và gỡ cài đặt.

**Doctor** (lệnh kiểm tra cài đặt) báo:

- **READY**: các skill bắt buộc, tùy chọn và hợp đồng đều đạt.
- **DEGRADED**: skill bắt buộc và hợp đồng đạt, nhưng thiếu một hoặc nhiều skill tùy chọn.
- **FAIL**: thiếu skill bắt buộc, skill không hợp lệ hoặc kiểm tra hợp đồng thất bại.

## Bắt đầu rà soát

Mở dự án đích trong agent rồi yêu cầu tự nhiên:

~~~text
Review requirement này giúp tôi.
~~~

Với dự án brownfield, có thể nói rõ:

~~~text
Hãy rà soát requirement này trên hệ thống hiện tại và chỉ ra các điểm còn thiếu hoặc chưa rõ.
~~~

Bạn không cần biết tên từng skill hay gọi chúng trực tiếp. BA Kit tự định tuyến yêu cầu, khám phá hệ thống hiện tại khi cần, phân biệt bằng chứng với quyết định và hỏi về các điểm chưa rõ có ảnh hưởng trọng yếu.

## Kết quả mong đợi

Tùy yêu cầu và quyết định của Human, công việc có thể tạo rà soát khoảng trống, câu hỏi còn mở, bản ghi quyết định, Business Rules đã duyệt, SRS chuẩn, sơ đồ hoặc tài liệu xuất. Tệp **workflow-state.json** trong dự án theo dõi tiến độ. Chỉ tạo Engineering Handoff sau khi Human phê duyệt rõ ràng BA baseline và không còn mục blocking.

**“Tiếp tục” không phải phê duyệt.** Xem [Quy trình](BA_KIT_WORKFLOW.md), [Hướng dẫn sử dụng](BA_KIT_USAGE_GUIDE.md), [ví dụ CR-001](../../kits/ba/examples/CR-001/README.md) và [FAQ](BA_KIT_FAQ.md).

## Trạng thái hiện tại

BA Kit là ứng viên RC1. Runtime acceptance cho package đang bị chặn vì isolated provider/runtime không trả lời; phát hành công khai bị chặn bởi vấn đề giấy phép và provenance chưa được giải quyết. Xem [Trạng thái phát hành](RELEASE.md) và [Nguồn gốc](PROVENANCE.md).

---

English: [Quick Start](../en/BA_KIT_QUICKSTART.md)
