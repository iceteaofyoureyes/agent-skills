# CR-001: Appointment Scheduling

**Ví dụ chỉ dành cho tài liệu.** Input ban đầu được cố ý để thiếu thông tin. Các tệp sau minh họa đầu ra rà soát và quyết định tình huống; chúng không phải câu trả lời runtime cố định hay bản golden.

> Không đưa các đầu ra đã duyệt trong thư mục này vào fresh-session acceptance. Với phiên acceptance mới, chỉ cung cấp input ban đầu cùng các đầu vào được phép; để agent tự tìm gap.

| Tệp | Phân loại ví dụ | Mục đích |
|---|---|---|
| [01-input-requirement.md](vi/01-input-requirement.md) | INPUT | Yêu cầu bắt đầu, cố ý chưa đầy đủ. |
| [02-gap-review.md](vi/02-gap-review.md) | ILLUSTRATIVE OUTPUT | Các câu hỏi và phần quyết định Human minh họa riêng. |
| [03-approved-business-rules.md](vi/03-approved-business-rules.md) | ILLUSTRATIVE OUTPUT | Business Rules ví dụ có truy vết; giá trị chưa xác nhận vẫn UNKNOWN. |
| [04-srs-excerpt.md](vi/04-srs-excerpt.md) | ILLUSTRATIVE OUTPUT | Yêu cầu chức năng minh họa và ranh giới kỹ thuật. |
| [05-engineering-handoff.yml](vi/05-engineering-handoff.yml) | CONTRACT-VALID EXAMPLE (minh họa) | Dùng đúng schema hiện tại; hash gắn với các nguồn ví dụ cùng thư mục. |

Quyết định sau gap review được đưa riêng làm ngữ liệu cho ví dụ; không suy ra chúng từ input ban đầu. ID Business Rules/requirement và câu chữ chỉ để minh họa. Hãy theo contract thật, source authority và Human Gate.

Hash trong handoff là SHA-256 thực của các tệp nguồn đi kèm. Nếu dùng lại cấu trúc này cho dự án, thay đường dẫn, revision và hash bằng artifact đã được duyệt của dự án đó. Ví dụ handoff không chứng minh CR-001 runtime acceptance đã đạt.

Bản hợp đồng hợp lệ giả định BA đã phân loại thời lượng tối đa chưa rõ và chi tiết danh sách là không blocking cho handoff ví dụ này. Các giá trị vẫn UNKNOWN; hạ nguồn không được tự quyết định. BA của dự án thật phải phân loại; nếu mục nào blocking thì không tạo handoff.

English: [CR-001 example](en/README.md)
