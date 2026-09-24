# Architecture

This repository keeps every atomic skill canonical at its root. `kits/ba/kit.yaml` is the single source for the BA role composition, including shared core capabilities. BA workflow orchestration lives in `ba-workflow/`; detailed procedures remain in atomic skills.

BA Kit answers WHAT the system needs to do, future Dev Kit answers WHERE + HOW after Engineering Impact and a Tech Lead gate, and future Test Kit proves the result. The future Dev flow is BA Handoff → Engineering Impact → Tech Lead Gate → Spec Kit → Plan → Tasks → Implementation → Review. Test Kit consumes the BA semantic baseline plus Dev technical evidence. Neither future kit is implemented here.

The installer uses the manifest as its only dependency source. Codex and Claude Code use their native Agent Skills directories; generic installs use an explicit directory. Skills Manager metadata remains independent and optional.
