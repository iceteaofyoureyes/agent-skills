# Trạng thái phát hành của suite

Phiên bản phản ánh [suite manifest](../../tooling/sdlc-suite.json) và manifest từng Kit. Acceptance nằm trong [suite acceptance](../../tooling/sdlc-suite-acceptance.yaml).

| Thành phần | Candidate | Ý nghĩa |
|---|---|---|
| Suite | agent-assisted-sdlc-vnext 1.0.0-rc.4 · INTERNAL_RC_CANDIDATE | Internal candidate để Human review |
| BA | 2.0.0-rc.6 | Package candidate |
| Dev | 0.4.0-rc.4 | Integration candidate |
| Test | 2.0.0-rc.14 | Package candidate |

Candidate source branch: docs/full-documentation-hardening-rc-gate. SHA/tree cuối được bind trong Public Cross-Kit Conformance. Đây chưa phải stable release; chưa có Git tag hay GitHub Release cho candidate này.

## Các lớp readiness

- **Package readiness:** Kit Doctor xác minh manifest, payload và required capability. READY không chứng minh project approval hay Test verification.
- **Suite compatibility:** Suite Doctor xác minh component versions, contract versions, routers, runtime và package authority.
- **Public Conformance:** chạy trên exact clean candidate SHA bằng fresh clone. PASS là evidence cho review. Optional projection gap được phép có thể ghi riêng OPTIONAL_DEGRADED.
- **Human release decision:** sau các gate trên, Human quyết định có tích hợp và phát hành hay không.
- **Git tag / GitHub Release:** chỉ tạo sau quyết định Human riêng; chưa thuộc candidate này.

VERIFIED là trạng thái cuối của product lifecycle. Merge/release cần Human quyết định riêng. Doctor READY, PROJECT_FOUNDATION_READY, READY_FOR_TEST, APPROVED_TESTWARE, EXECUTION_READY hay conformance PASS không thay quyết định đó. Xem [readiness glossary](READINESS_STATES.md).

## Đường review candidate

1. Xác minh package bằng [installation và Kit Doctors](INSTALLATION.md).
2. Chạy [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md) trên đúng SHA đã commit.
3. Bind SHA/tree, package digests, Doctor outputs và conformance report vào Human review.
4. Dừng trước merge, tag hoặc release cho tới khi Human ra quyết định riêng.

---

English: [Suite release status](../en/RELEASE.md)
