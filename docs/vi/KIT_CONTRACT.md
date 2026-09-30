# Hợp đồng chung của Kit

- Mỗi Kit có `kits/<id>/kit.yaml`: id/version, workflow entry skill, core/required/optional skills và các capability/dependency/prerequisite được khai báo. `skill_sources` chỉ rõ thư mục nguồn khi skill không ở root; `files` là allowlist source → destination của regular files. Không copy wildcard.
- Installer generic hỗ trợ install, doctor, reinstall và uninstall theo `--agent`, `--scope` hoặc `--target`; BA và Test dùng install record/managed paths riêng. File người dùng sửa được giữ lại và report drift, không bị im lặng ghi đè. Uninstall không xóa asset của Kit khác hoặc file không thuộc Kit.
- Manifest có thể khai báo `integrity.authority` và `integrity.payload`. Với Kit dùng integrity, installed `.<kit-id>-kit/kit.yaml` là local package-definition root; authority file giữ expected payload inventory, SHA-256 và classification; install record giữ ownership/state. Doctor kiểm tra pin trong manifest, authority, record và actual managed bytes theo thứ tự. Root definition không tự chứng minh tính xác thực mật mã của chính nó.
- Payload digest chỉ bao gồm resolved runtime payload; root definition, authority và install record thuộc digest domain khác để tránh tự tham chiếu. Chi tiết [packaging contract](../../tooling/PACKAGING.md).
- BA legacy manifest không có integrity anchors vẫn được hỗ trợ. BA `workflow-state.json` và `engineering-handoff.yml` tiếp tục được validator kiểm tra; thiếu optional BA skill có thể báo `DEGRADED`.
- `READY` của Doctor chứng minh các contract mà Kit đó khai báo đạt tại thời điểm kiểm tra; nó không là Human approval hoặc kết quả chạy nghiệp vụ. `FAIL` cần được xử lý trước khi coi package healthy. Human Gate thuộc workflow của từng Kit, không thuộc installer.

Xem [BA Kit](../../kits/ba/README.md), [Test Kit capabilities](TEST_KIT_CAPABILITIES.md) và [cài đặt](INSTALLATION.md).

---

English: [Kit contract](../en/KIT_CONTRACT.md)
