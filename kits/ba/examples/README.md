# BA Kit examples

Try the kit with ordinary requests:

- `Review requirement này giúp tôi.`
- `Tiếp tục.`
- `Viết SRS cho quyết định BA đã xác nhận.`
- `Update tài liệu theo thay đổi đã được BA duyệt.`

The workflow reads project state and routes internally. Do not write `APPROVE` unless the Human intends to approve the named artifact. Use `kits/ba/acceptance.yaml` for the acceptance cases; no sample business decisions are invented here.
