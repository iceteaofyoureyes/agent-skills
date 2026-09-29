import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tooling.lib import codex_cli
from tooling.tests.codex_stub import fake_codex_on_path


class CodexCliResolverTests(unittest.TestCase):
    def test_temporary_path_command_is_resolved_without_global_codex(self):
        with fake_codex_on_path() as (command_path, capture_path):
            resolved = codex_cli.resolve_codex_command()
            self.assertEqual(resolved.resolution, "PATH")
            self.assertEqual(
                Path(resolved.target),
                (command_path.parent / "node_modules/@openai/codex/bin/codex.js").resolve(),
            )
            self.assertNotIn("nvm4w", " ".join(resolved.argv_prefix).casefold())

    def test_explicit_override_with_spaces_is_used_and_preserves_argument_boundaries(self):
        with fake_codex_on_path() as (path_command, capture_path):
            override_dir = path_command.parent.parent / "Explicit Override With Spaces"
            override_dir.mkdir()
            override = override_dir / path_command.name
            override.write_bytes(path_command.read_bytes())
            shutil.copytree(path_command.parent / "node_modules", override_dir / "node_modules")
            with mock.patch.dict(os.environ, {codex_cli.CODEX_COMMAND_ENV: str(override)}):
                resolved = codex_cli.resolve_codex_command()
                arguments = ["exec", "--model", "model name with spaces", "-o", str(override_dir / "output file.md")]
                process = subprocess.run(
                    resolved.argv(arguments), input=b"test prompt", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    check=False,
                )

            self.assertEqual(process.returncode, 0, process.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(resolved.resolution, codex_cli.CODEX_COMMAND_ENV)
            self.assertEqual(
                Path(resolved.target),
                (override_dir / "node_modules/@openai/codex/bin/codex.js").resolve(),
            )
            self.assertEqual(json.loads(capture_path.read_text(encoding="utf-8")), arguments)
            self.assertTrue((override_dir / "output file.md").is_file())

    def test_invalid_explicit_override_fails_without_path_fallback(self):
        with fake_codex_on_path() as (path_command, _capture_path):
            missing = path_command.parent / "missing Codex command.ps1"
            with mock.patch.dict(os.environ, {codex_cli.CODEX_COMMAND_ENV: str(missing)}):
                with self.assertRaises(codex_cli.CodexDependencyError) as error:
                    codex_cli.resolve_codex_command()

        self.assertEqual(error.exception.code, "CODEX_INVALID_OVERRIDE")
        self.assertIn(codex_cli.CODEX_COMMAND_ENV, str(error.exception))
        self.assertIn("PATH fallback was not attempted", str(error.exception))

    def test_missing_codex_fails_closed_with_operator_instructions(self):
        with tempfile.TemporaryDirectory() as empty_path:
            with mock.patch.dict(os.environ, {"PATH": empty_path, codex_cli.CODEX_COMMAND_ENV: ""}):
                with self.assertRaises(codex_cli.CodexDependencyError) as error:
                    codex_cli.resolve_codex_command()

        self.assertEqual(error.exception.code, "CODEX_MISSING_DEPENDENCY")
        self.assertIn("Codex CLI is required", str(error.exception))
        self.assertIn("available on PATH", str(error.exception))
        self.assertIn(codex_cli.CODEX_COMMAND_ENV, str(error.exception))

    def test_standard_npm_cmd_shim_resolves_to_node_and_pinned_entrypoint_without_shell(self):
        for suffix, wrapper in (
            (".cmd", '@echo off\n"%dp0%\\node_modules\\@openai\\codex\\bin\\codex.js" %*\n'),
            (".ps1", "$basedir/node_modules/@openai/codex/bin/codex.js $args\n"),
        ):
            with self.subTest(launcher=suffix), tempfile.TemporaryDirectory(prefix="Codex npm shim with spaces ") as temp:
                root = Path(temp)
                launcher = root / f"codex{suffix}"
                script = root / "node_modules/@openai/codex/bin/codex.js"
                node = root / "node.exe"
                script.parent.mkdir(parents=True)
                script.write_text("// pinned CLI stub\n", encoding="utf-8")
                node.write_bytes(b"node placeholder")
                launcher.write_text(wrapper, encoding="utf-8")
                with mock.patch.dict(os.environ, {codex_cli.CODEX_COMMAND_ENV: str(launcher)}):
                    resolved = codex_cli.resolve_codex_command()

                self.assertEqual(resolved.argv_prefix, (str(node), str(script)))
                self.assertNotIn("cmd.exe", " ".join(resolved.argv_prefix).casefold())

    def test_explicit_codex_js_override_uses_node_from_path(self):
        with tempfile.TemporaryDirectory(prefix="Codex JS override with spaces ") as temp:
            script = Path(temp) / "codex entrypoint.js"
            script.write_text("// test entrypoint\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {codex_cli.CODEX_COMMAND_ENV: str(script)}):
                with mock.patch.object(
                    codex_cli.shutil, "which",
                    side_effect=lambda name: "node-on-path" if name in {"node", "node.exe"} else None,
                ):
                    resolved = codex_cli.resolve_codex_command()

        self.assertEqual(resolved.argv_prefix, ("node-on-path", str(script.resolve())))
        self.assertEqual(resolved.resolution, codex_cli.CODEX_COMMAND_ENV)
