# Câu hỏi thường gặp

## Tôi có phải cài cả BA, Dev và Test Kit không?

Không. Chỉ cài Kit phù hợp với công việc. Dùng cả ba khi muốn chạy lifecycle BA → Dev → Test đầy đủ.

## Chỉ dùng Dev Kit được không?

Được, nếu authority/business input bắt buộc đã tồn tại và được duyệt. Dev không được tự phát minh WHAT còn thiếu; phần business chưa rõ phải route upstream.

## Chỉ dùng Test Kit được không?

Được khi Test có authority input mà Test contract hiện tại yêu cầu. Full flow có thể cung cấp thêm Dev technical context, nhưng Dev không cấp business authority cho Test.

## Project Foundation có phải Kit thứ tư không?

Không. Đây là shared workflow/capability để bootstrap hoặc recover project context.

## Dùng được cho project đang maintain không?

Được. Brownfield recovery là use case chính. Code/behavior hiện tại là evidence về CURRENT_SYSTEM, không tự động trở thành target behavior được duyệt.

## Dùng được cho greenfield không?

Được. Foundation có thể bootstrap target project context; business behavior vẫn thuộc BA/Human approval.

## Agent có tự approve không?

Không. \`CONTINUE\`, \`ANSWER\`, validator PASS, Doctor READY và generated artifact đều không phải approval.

## Doctor READY có nghĩa gì?

Package đã cài và required capability hợp lệ. Nó không có nghĩa feature approved, test PASS, VERIFIED hay sẵn sàng release.

## READY_FOR_TEST là gì?

Dev handoff state: Engineering đã có implementation/review/verification evidence cần thiết để Test tiếp nhận. Nó không phải Tester verification.

## APPROVED_TESTWARE là gì?

Canonical Testcases/trace đã được Human duyệt. Nó chưa phải automation readiness và chưa phải execution PASS.

## EXECUTION_READY là gì?

Automation/execution input đã được review và bind. Test chưa nhất thiết đã chạy.

## VERIFIED lúc nào cũng phải retest à?

Không. Initial execution sạch có thể đi thẳng tới Tester VERIFIED khi mọi Observation bắt buộc PASS và không còn Finding mở. Retest chỉ bắt buộc sau defect/fix path.

## VERIFIED có nghĩa merge luôn không?

Không. VERIFIED kết thúc product-verification lifecycle của framework. Merge/release là quyết định Human riêng.

## Command test fail thì có tự thành DEFECT không?

Không. Command result chỉ là evidence. Tester phải đối chiếu approved oracle rồi classify Finding.

## Dev gặp requirement chưa rõ thì sao?

Route upstream gap; không tự quyết business WHAT.

## XMind có bắt buộc không?

Không. Đây là optional projection. Test core vẫn có thể dùng khi XMind thiếu nếu Doctor/conformance báo đúng trạng thái optional degradation.

## Hỗ trợ agent runtime nào?

Đường end-to-end được verify chính hiện là Codex. BA còn có Claude Code và generic installation target theo tài liệu. Không mặc định mọi full cross-Kit path đều đã được verify tương đương trên mọi agent runtime.

## Dùng Python bản nào?

Dùng Python **3.10+** cho baseline BA/Test và cấu hình full toolkit đơn giản nhất. Chi tiết từng capability ở [Cài đặt](INSTALLATION.md).

## Vẫn thấy nhiều thuật ngữ thì đọc gì trước?

Đọc [Bắt đầu](GETTING_STARTED.md), rồi [Ví dụ Full Flow](FULL_FLOW_EXAMPLE.md). Sau đó mới cần xuống [Kiến trúc](ARCHITECTURE.md) và [Readiness states](READINESS_STATES.md).
