# CR-001 — Hướng dẫn Test Design

- Xem xét boundary/negative coverage cho approved FR/BR, giữ trace nguyên vẹn.
- Với rule khoảng nửa mở đã duyệt, phân tích touching boundary và overlap condition; không invent business outcome ngoài BA.
- Với duration > 0 đã duyệt, xem xét zero/negative condition; maximum duration vẫn UNKNOWN.
- Scenario phụ thuộc maximum duration hoặc filter/sort/pagination chưa được BA quyết định phải giữ UNKNOWN/deferred, không assertion cụ thể.
- Priority/risk chỉ là advisory; không đưa field ngoài canonical Design schema.
