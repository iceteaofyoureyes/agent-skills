# CR-001 — Quy ước manual testcases

- Giữ testcase ID theo frozen raw profile TC-... và exact approved Design ID trong trace.
- Đặt name theo `CR-001 - <hành vi> - <điều kiện>`, ví dụ `CR-001 - Tạo lịch hẹn - Hai lịch chạm nhau`.
- Viết objective, preconditions, actions và expected results bằng tiếng Việt; giữ business wording đúng authority.
- Mỗi case tập trung một điều kiện và có flow self-contained. Decomposition chỉ trong approved Design scenario boundary.
- Xem xét boundary và negative variants nếu đã nằm trong approved coverage; không thêm business behavior.
- Dữ liệu chung ở testcase scope, dữ liệu step chỉ khi source nêu rõ. Không đoán test data.
- Priority chỉ P0–P3, advisory; giữ material OPEN execution dependencies khi thiếu approved setup/action/observation oracle.
- Maximum duration UNKNOWN không được biến thành expected result 120 phút.
