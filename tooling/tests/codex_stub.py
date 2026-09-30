"""Temporary deterministic Codex command used by invocation portability tests."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from tooling.lib.codex_cli import CODEX_COMMAND_ENV


_NODE_STUB = r"""const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);
fs.writeFileSync(process.env.CODEX_STUB_CAPTURE, JSON.stringify(args), 'utf8');
let prompt = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { prompt += chunk; });
process.stdin.on('end', () => {
  const index = args.indexOf('-o');
  if (index >= 0) {
    const target = args[index + 1];
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, 'workflowStatus: completed\n# deterministic stub\n', 'utf8');
    if (target.endsWith('agent-final.md')) {
      const cases = path.join(process.cwd(), 'output', 'test-cases.md');
      fs.mkdirSync(path.dirname(cases), { recursive: true });
      fs.writeFileSync(cases, '# Native Katalon stub\n', 'utf8');
    }
  }
  process.stdout.write('{"type":"message","message":"deterministic Codex stub"}\n');
});
"""


_PYTHON_STUB = r"""import json, os, pathlib, sys
args = sys.argv[1:]
pathlib.Path(os.environ['CODEX_STUB_CAPTURE']).write_text(json.dumps(args), encoding='utf-8')
sys.stdin.read()
if '-o' in args:
    target = pathlib.Path(args[args.index('-o') + 1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('workflowStatus: completed\n# deterministic stub\n', encoding='utf-8')
    if target.name == 'native-agent-final.md':
        output = pathlib.Path.cwd() / 'output/test-cases.md'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('# Native Katalon stub\n', encoding='utf-8')
print('{"type":"message","message":"deterministic Codex stub"}')
"""


@contextmanager
def fake_codex_on_path():
    temporary = tempfile.TemporaryDirectory(prefix="Test Kit Codex Stub With Spaces ")
    root = Path(temporary.name)
    binary_dir = root / "Codex CLI Stub With Spaces"
    binary_dir.mkdir()
    capture = root / "captured invocation.json"
    if os.name == "nt":
        command = binary_dir / "codex.cmd"
        script = binary_dir / "node_modules/@openai/codex/bin/codex.js"
        script.parent.mkdir(parents=True)
        script.write_text(_NODE_STUB, encoding="utf-8")
        command.write_text(
            '@ECHO off\n"%dp0%\\node_modules\\@openai\\codex\\bin\\codex.js" %*\n',
            encoding="utf-8",
        )
        node = shutil.which("node.exe") or shutil.which("node")
        if node is None:
            temporary.cleanup()
            raise RuntimeError("Node.js is required for the Windows Codex shim stub test")
        # Execute the fake package from this temporary PATH without using a global Codex shim.
        shutil.copyfile(node, binary_dir / "node.exe")
        path = str(binary_dir)
    else:
        command = binary_dir / "codex"
        command.write_text(f"#!{sys.executable}\n" + _PYTHON_STUB, encoding="utf-8")
        command.chmod(0o755)
        path = os.pathsep.join((str(binary_dir), str(Path(sys.executable).parent)))

    try:
        with mock.patch.dict(os.environ, {
            "PATH": path,
            CODEX_COMMAND_ENV: "",
            "CODEX_STUB_CAPTURE": str(capture),
        }):
            yield command, capture
    finally:
        temporary.cleanup()
