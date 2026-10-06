# Dev Kit VNext — Provenance và Package Integrity

Dev Kit VNext là prerelease `0.4.0-rc.4`, được cài vào
`~/.devkit/runtime/v2`. Version ở `kits/dev/kit.yaml` và plugin metadata phải
khớp. Đây không phải stable release.

## Runtime và authority dependencies

| Thành phần | Pin hiện tại | Vai trò |
|---|---|---|
| GitHub Spec Kit | `v1.0.11`, commit `8147943512404afb9d99c6252cb9bf84369fd0b0` | Workflow state, pause/resume và bundle transport; không phát sinh WHAT hoặc technical approval |
| Codebase Memory MCP | `v0.11.0`, commit `8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798` | Tùy chọn khi blast radius chưa rõ |
| BA VNext reader | `ba_vnext.py`, `ba_contracts.py` cùng BA proof dependencies | Xác thực Engineering Handoff VNext và exact `APPROVED_BASELINE` proof |
| Shared SDLC/Foundation | `shared/sdlc/` modules trong package manifest | Schema, authority, Foundation proof, topology, impact và provenance contracts |

Spec Kit không được gọi cho `speckit.specify`, `plan`, `tasks`, `analyze` hoặc
`converge`. Workflow choice không phải Human/Tech Lead technical receipt.
Delivery Manifest giữ `DEFERRED_NON_AUTHORITATIVE`.

## Plugin provenance

- Addy Agent Skills `0.6.10`, commit
  `c004a74784a08295d52749b04cda634125b9a581`, MIT. Chín engineering skills và
  năm shared references giữ exact upstream blobs; `planning-and-task-breakdown`
  chỉ có hai policy-line thay đổi để Human gate phụ thuộc risk.
- Superpowers `review-package`, release `v6.4.1`, commit
  `5bf4e78011075bcfc0dc295f0724994cd123ee71`, MIT; utility giữ exact upstream
  blob.
- Canonical `verification-before-completion`, local provenance commit
  `3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b`, giữ nguyên.
- Canonical `requirements-gap-auditor`, commit
  `1fe1950bc4759e732b036c562b0cff99675e1695`, giữ nguyên.

License copies và notices nằm trong plugin package và ở
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md). Wave 3 không nâng cấp
third-party dependencies.

## Package identity và hash closure

`tooling/install_dev_kit.py` cài payload allowlist vào runtime/v2, ghi
`install-manifest.json` với schema/runtime/version, từng file SHA-256, Python
executable và launcher. Runtime inventory loại trừ đúng manifest tự thân; Doctor
đối chiếu toàn bộ installed file set và bytes với inventory.

`kits/dev/provenance.lock.json` ghi exact source payload hashes bằng
`DEV_RUNTIME_PACKAGE_SHA256_V2`; provenance lock tự loại khỏi digest để tránh
self-reference. `tooling/regenerate_dev_provenance.py` dùng package file list
của installer. Upstream version, commit, license và selected blob locks vẫn giữ
nguyên.

V2 schemas được xuất từ executable contracts bằng
`python -I tooling/regenerate_dev_vnext_schemas.py`; Doctor và contract tests
phát hiện drift. V1 schemas/templates vẫn là `LEGACY_COMPAT` và không bị ghi đè.

## Kiểm tra

```text
python -m unittest tooling.tests.test_dev_kit -v
python -m unittest tooling.tests.test_dev_vnext -v
python -m unittest tooling.tests.test_dev_vnext_runtime -v
python -m unittest tooling.tests.test_dev_vnext_runtime_acceptance -v
python -m unittest tooling.tests.test_dev_vnext_cli -v
python -m unittest tooling.tests.test_dev_vnext_spec_kit -v
python -m unittest tooling.tests.test_dev_vnext_installed_acceptance -v
python -m unittest tooling.tests.test_ba_vnext_installed_acceptance -v
```

Installed acceptance phải PASS trước khi công bố Dev package readiness. Doctor
`READY` chỉ báo `PACKAGE/CAPABILITY READY`; chỉ Dev lifecycle tạo
`READY_FOR_TEST` handoff readiness.
