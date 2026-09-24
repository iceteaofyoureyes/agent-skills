# Tổng quan kiến trúc

Các skill nguyên tử được lưu canonical ở thư mục gốc. **kits/ba/kit.yaml** là nguồn duy nhất mô tả thành phần BA Kit. **ba-workflow/** điều phối yêu cầu và giữ ranh giới trạng thái/phê duyệt; các skill nguyên tử thực hiện quy trình khám phá, phân tích, SRS, sơ đồ và tài liệu chi tiết.

## Phân chia trách nhiệm

| Giai đoạn | Câu hỏi | Trạng thái |
|---|---|---|
| BA Kit | **WHAT** — hệ thống cần làm gì? | Ứng viên RC1; runtime functional acceptance đang bị chặn. |
| Engineering Impact (phân tích tác động kỹ thuật) | Công việc thuộc **WHERE** và **WHO** sở hữu? | Planned; chưa triển khai. |
| Dev Kit + Spec Kit | **HOW** — thiết kế và xây dựng thế nào? | Planned; chưa triển khai. |
| Test Kit + TEA (khả năng kiểm thử hạ nguồn) | **HOW DO WE PROVE IT** — chứng minh hoạt động ra sao? | Planned; chưa triển khai. |

Luồng dự kiến: Requirement → BA Kit → Approved BA Baseline → Engineering Impact → Dev Kit + Spec Kit → Test Kit + TEA. Lộ trình chi tiết sau BA gồm Engineering Handoff (bàn giao BA cho kỹ thuật) → Engineering Impact → Tech Lead Gate → Spec Kit → lập kế hoạch/triển khai → Test Kit/TEA. Hiện chỉ BA Kit được đóng gói thành Kit; các giai đoạn tương lai phải giữ nguyên ngữ nghĩa BA đã duyệt và giải quyết quyết định kỹ thuật ở hạ nguồn.

Installer chỉ đọc dependency từ manifest. Codex và Claude Code dùng thư mục Agent Skills native; generic cần chỉ rõ thư mục. Metadata Skills Manager độc lập và không bắt buộc. Xem [Cài đặt](INSTALLATION.md), [Hợp đồng Kit](KIT_CONTRACT.md) và [Nguồn gốc](PROVENANCE.md).

---

English: [Architecture](../en/ARCHITECTURE.md)
