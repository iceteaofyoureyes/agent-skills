# Provenance và quyền phân phối của BA Kit RC1

## Cơ sở kiểm toán

- Repository cần kiểm tra: nhánh feature/ba-kit-rc1-packaging. Tác vụ bắt đầu tại HEAD 31dd25333fdcd9d3763ebba7b60ee6c37d42c8e1 với worktree có thay đổi: tài liệu bản địa hóa, provenance và license. Không có thay đổi ban đầu nào bị loại bỏ.
- Benchmark được kiểm tra ở chế độ chỉ đọc tại nhánh benchmark/agent-skills-v1-vi, commit b7d8d63c80c8fb2156b5267804f4081e60b51f76. Tệp chưa được track từ trước benchmark/input/templates/SRS_TEMPLATE.docx được giữ nguyên.
- Lịch sử Git của cả hai repository được kiểm tra trước khi đối chiếu các ứng viên công khai. Khi phù hợp, nội dung được so sánh theo commit, cây tệp, hash, diff đã chuẩn hóa và đoạn văn bản đặc trưng.
- Manifest của BA Kit là kits/ba/kit.yaml. tooling/lib/ba_kit.py cài ba-workflow, hai skill core, toàn bộ skill required và các skill optional hiện có bằng cách sao chép thư mục skill. THIRD_PARTY_NOTICES.md là danh mục thông báo cấp repository.
- Phân loại: EXACT_UPSTREAM, MODIFIED_UPSTREAM, PROJECT_OWNED, UNKNOWN. Trạng thái phân phối: READY, READY_WITH_ATTRIBUTION, BLOCKED_UNKNOWN_ORIGIN, BLOCKED_LICENSE, NOT_DISTRIBUTED.

## BA Kit: required và core

| Thành phần; vai trò; đường dẫn local | Nguồn và đường dẫn upstream | License và copyright | Thay đổi local; tệp license / notice | Bằng chứng | Phân phối |
|---|---|---|---|---|---|
| ba-workflow; workflow; ba-workflow/ | PROJECT_OWNED; được tạo trong repository này qua các commit 524f7f8, 982b1b6 và 31dd253; không có upstream | Human đã duyệt MIT; chưa thêm LICENSE gốc và license độc lập cho workflow | Workflow, reference, template và validator do dự án viết. Hiện chưa có tệp license. | Lịch sử Git của target và manifest; installer sao chép thư mục này như một skill. | BLOCKED_LICENSE |
| verification-before-completion; core; verification-before-completion/ | EXACT_UPSTREAM; obra/superpowers, skills/verification-before-completion; commit nội dung 3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b; HEAD upstream hiện tại 5bf4e78011075bcfc0dc295f0724994cd123ee71 | MIT; Copyright (c) 2025 Jesse Vincent | Nội dung không đổi sau khi chuẩn hóa line ending. Có LICENSE upstream. | .skills-manager ghi repository và path; nội dung local khớp blob upstream. | READY_WITH_ATTRIBUTION |
| codebase-discovery; core; codebase-discovery/ | EXACT_UPSTREAM; DiUS/agent-toolkit, skills/codebase-discovery; d43b664e2860f7a5dd5b8ae892c44fdfc5ae9dfc | MIT; Copyright (c) 2026 DiUS | Khớp cả 31 tệp. Ghi công Bryan Signey vẫn còn trong SKILL.md. Có LICENSE upstream. | Benchmark thêm cây tệp tại 709916a0; các tệp local khớp cây và commit nội dung ứng viên. | READY_WITH_ATTRIBUTION |
| requirements-gap-auditor; required; requirements-gap-auditor/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, .agents/skills/requirements-gap-auditor/SKILL.md; 1fe1950bc4759e732b036c562b0cff99675e1695 | MIT; LICENSE upstream ghi Copyright (c) 2026 nhưng không nêu chủ sở hữu | Chỉ thêm description frontmatter cho Agent Skills; phần thân sau chuẩn hóa giống hệt. Có LICENSE trong thư mục skill. | Benchmark thêm skill lần đầu tại 709916a0; phần thân local đã chuẩn hóa khớp tệp upstream. | READY_WITH_ATTRIBUTION |
| requirements-interrogator; required; requirements-interrogator/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, .agents/skills/requirements-interrogator/SKILL.md; 1fe1950bc4759e732b036c562b0cff99675e1695 | MIT; LICENSE upstream ghi Copyright (c) 2026 nhưng không nêu chủ sở hữu | Chỉ thêm description frontmatter cho Agent Skills; phần thân sau chuẩn hóa giống hệt. Có LICENSE trong thư mục skill. | Benchmark thêm skill lần đầu tại 709916a0; phần thân local đã chuẩn hóa khớp tệp upstream. | READY_WITH_ATTRIBUTION |
| requirements-quality-check; required; requirements-quality-check/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, quality/requirements-quality-check/SKILL.md; 6114b14d939622ff38b971198e2f064ac1aa11df | MIT; LICENSE upstream ghi Copyright (c) 2026 nhưng không nêu chủ sở hữu | Chỉ thêm name và description frontmatter; phần thân sau chuẩn hóa giống hệt. Có LICENSE trong thư mục skill. | Benchmark thêm skill tại 457bfa1; phần thân local khớp nguồn và bản mirror trong benchmark. | READY_WITH_ATTRIBUTION |
| business-rule-extractor; required; business-rule-extractor/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, .agents/skills/business-rule-extractor/SKILL.md; 1fe1950bc4759e732b036c562b0cff99675e1695 | MIT; LICENSE upstream ghi Copyright (c) 2026 nhưng không nêu chủ sở hữu | Chỉ thêm description frontmatter cho Agent Skills; phần thân sau chuẩn hóa giống hệt. Có LICENSE trong thư mục skill. | Benchmark thêm skill tại 457bfa1; phần thân local đã chuẩn hóa khớp tệp upstream. | READY_WITH_ATTRIBUTION |
| srs-function-document; required; srs-function-document/ | UNKNOWN; path .agents/skills/srs-function-document/SKILL.md trong benchmark xuất hiện lần đầu tại 457bfa18d6e9ffe246d9ab2940c036996ec365a4; chưa xác lập revision upstream | Chưa biết license và chủ sở hữu copyright | Không có LICENSE hay ghi nguồn. Implementation hiện tại chưa đủ điều kiện phân phối. | Blob của target và benchmark giống nhau tại fe6b2c9086acd232ac6fe4c8d0d14c66faa714c2. Không có source record hay URL cài đặt trong .skills-manager. Lịch sử chỉ chứng minh thời điểm được track lần đầu, không chứng minh tác giả. Tìm kiếm công khai chính xác chưa xác lập được nguồn. | BLOCKED_UNKNOWN_ORIGIN |
| document-docx; required; document-docx/ | MODIFIED_UPSTREAM; vasilyu1983/AI-Agents-public, frameworks/shared-skills/skills/document-docx; da9d28fd0f5427f18a15d3fb363ab3651e6625ca | MIT; Copyright (c) 2025-2026 Vasiliy Uvarov | Đã bỏ tệp học tập và cache sinh tự động; chuyển workflow học tập và skill liên quan thành optional; bỏ liên kết sibling không có sẵn; hai script chỉ khác dòng trống cuối tệp. Có LICENSE trong thư mục skill. | Benchmark đưa vào tại 2c4355d với 23 tệp; 22 blob ID khớp snapshot ứng viên. | READY_WITH_ATTRIBUTION |
| drawio-skill; required; drawio-skill/ | EXACT_UPSTREAM; Agents365-ai/drawio-skill, skills/drawio-skill; 7aa92f73819766eb914fffac66762cf2adb5d828 | MIT; Copyright (c) 2026 Agents365-ai | Cây tệp khớp release 3.4.0. Giữ LICENSE và metadata tác giả/trang chủ hiện có. | Benchmark thêm skill tại 457bfa1; path và version upstream có trong metadata skill; đối chiếu cây tệp khớp. | READY_WITH_ATTRIBUTION |

## BA Kit: skill optional

| Thành phần; vai trò; đường dẫn local | Nguồn và đường dẫn upstream | License và copyright | Thay đổi local; tệp license / notice | Bằng chứng | Phân phối |
|---|---|---|---|---|---|
| product-design-and-ux; optional; product-design-and-ux/ | EXACT_UPSTREAM; magnus919/agent-skills, product-design-and-ux; 035e58d3e39690361596901ab8f17222ab9baf02 | MIT; Copyright (c) 2026 Magnus Hedemark | Khớp cả 19 tệp. Có LICENSE trong thư mục skill. | .skills-manager ghi repository và path nguồn; từng tệp local đều khớp. | READY_WITH_ATTRIBUTION |
| frontend-design; optional; frontend-design/ | EXACT_UPSTREAM; anthropics/skills, skills/frontend-design; 34040c9c568585f6929bedeaad110ad08f079624 | Apache-2.0; LICENSE.txt không nêu chủ sở hữu copyright | Cả hai tệp, gồm LICENSE.txt, đều khớp. | .skills-manager ghi path nguồn; cây hai tệp và blob đều khớp. | READY_WITH_ATTRIBUTION |
| impeccable; optional; impeccable/ | MODIFIED_UPSTREAM; pbakaus/impeccable, .agents/skills/impeccable; 53 tệp từ cd12f8660e2dde57b9615c8a6b8ea674101f9cfc (4.3.1), ba reference từ 6a93a352936ac7fbb1898a239ddae1f8c3828150 (4.4.0) | Apache-2.0; Copyright 2025 Paul Bakaus. NOTICE upstream ghi ios.md và android.md dùng tài liệu tham khảo từ ehmo/platform-design-skills theo MIT. | adapt.md, audit.md và harden.md có phần bổ sung local đã ghi nhận. Có LICENSE và NOTICE upstream. | .skills-manager ghi path upstream và version 4.3.1; 53/56 tệp khớp 4.3.1, ba tệp còn lại khớp 4.4.0. | READY_WITH_ATTRIBUTION |
| playwright; optional; playwright/ | EXACT_UPSTREAM; openai/skills, skills/.curated/playwright; 49f948faa9258a0c61caceaf225e179651397431 | Apache-2.0; Copyright (c) Microsoft Corporation | Cây chín tệp khớp; LICENSE.txt chỉ khác line ending. Giữ NOTICE.txt upstream, ghi công microsoft/playwright-cli và skills/playwright-cli/SKILL.md; notice không nêu revision của dependency này. | .skills-manager ghi path nguồn OpenAI; SKILL.md local và các tệp còn lại khớp cây nguồn. | READY_WITH_ATTRIBUTION |
| web-accessibility; optional; web-accessibility/ | EXACT_UPSTREAM; magnus919/agent-skills, web-accessibility; f7819d0f2048d1b71e0c261c660476965aa26602 | MIT; Copyright (c) 2026 Magnus Hedemark | Khớp cả 17 tệp. Có LICENSE trong thư mục skill. | .skills-manager ghi repository và path nguồn; từng tệp local đều khớp. | READY_WITH_ATTRIBUTION |

## Nội dung repository khác

Phạm vi nội dung project-owned do Human chọn gồm ba-workflow/, kits/, tooling/, docs/, core/, README do repository sở hữu và ví dụ do dự án viết. Lịch sử target ghi nhận các nội dung này tại commit 524f7f8, 982b1b6 và 31dd253. Human đã duyệt MIT, nhưng chưa thêm LICENSE gốc và ba-workflow/LICENSE độc lập; trong snapshot kiểm toán này các bản sao project-owned vẫn ở trạng thái BLOCKED_LICENSE. License gốc sẽ không thay đổi license của thành phần bên thứ ba.

Skill webapp-testing/ nằm ngoài BA Kit. Cây sáu tệp, gồm LICENSE.txt, khớp anthropics/skills tại 34040c9c568585f6929bedeaad110ad08f079624; tệp Apache-2.0 ghi Copyright 2026 Anthropic, PBC.

Phát hành toàn repository vẫn bị chặn vì các skill ngoài BA chưa được kiểm tra nội dung theo commit và chưa xác nhận gói license:

- addyosmani/agent-skills: api-and-interface-design, ci-cd-and-automation, code-review-and-quality, constraint-driven-development, documentation-and-adrs, observability-and-instrumentation, performance-optimization, security-and-hardening, shipping-and-launch và test-driven-development.
- vercel-labs/agent-skills: web-design-guidelines và vercel-react-best-practices. web-design-guidelines khớp upstream hiện tại tại commit 063bee94c3f4df8453406c830b0a7df0f2860278; README upstream công bố MIT nhưng skill local chưa có LICENSE.
- magnus919/agent-skills: product-discovery và product-methodology.
- obra/superpowers: systematic-debugging.
- nextlevelbuilder/ui-ux-pro-max-skill: ui-ux-pro-max.
- mattpocock/skills: to-spec.

Thư mục .skills-manager/ đang được Git track và đã được tạo/cập nhật trong các commit auto-backup, gồm các commit từ 9ea9b6d đến 3ea1b84. Schema ghi created_by: skills-manager. Thư mục chứa source reference và metadata scenario/skill, nhưng chưa xác định được phạm vi tác giả và license; source record cũng không pin revision nội dung. Installer BA Kit không sao chép cây thư mục này nên nó nằm ngoài payload BA Kit. Tuy nhiên Git vẫn phân phối các tệp đã track này; đây là blocker phát hành toàn repository cho đến khi có quyết định về ownership/license hoặc phạm vi công bố.

## Blocker hiện tại

- srs-function-document đang BLOCKED_UNKNOWN_ORIGIN. Human đã cho phép viết lại hành vi thành implementation project-owned dựa trên contract BA Kit; implementation cũ chưa được thay trong snapshot kiểm toán này.
- Nội dung BA Kit do dự án sở hữu đang BLOCKED_LICENSE cho đến khi thêm các tệp MIT đã duyệt.
- Các skill ngoài BA được liệt kê ở trên chặn việc phát hành toàn repository.

License MIT của dự án không cấp lại license cho bất kỳ skill bên thứ ba nào.
