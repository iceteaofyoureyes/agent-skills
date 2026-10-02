import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tooling.lib import dev_kit


class ExecutableResolutionTests(unittest.TestCase):
    def test_windows_bare_and_explicit_cmd_keep_arguments(self):
        for name in ("npm", "npm.cmd"):
            argv = [name, "run", "build", "a path & special"]
            with patch.object(dev_kit, "_WINDOWS", True), patch.object(dev_kit.shutil, "which", return_value=r"C:\Program Files\node\npm.CMD") as which:
                self.assertEqual(dev_kit.resolve_executable_argv(argv), [r"C:\Program Files\node\npm.CMD", *argv[1:]])
                which.assert_called_once_with(name)
            self.assertEqual(argv[0], name)

    def test_explicit_paths_are_not_rewritten(self):
        for name in (r"C:\node\npm.cmd", r".\node\npm.cmd", "./node/npm.cmd", "/usr/bin/npm"):
            with patch.object(dev_kit, "_WINDOWS", True), patch.object(dev_kit.shutil, "which") as which:
                self.assertEqual(dev_kit.resolve_executable_argv([name, "x"]), [name, "x"])
                which.assert_not_called()

    def test_posix_preserves_bare_command(self):
        with patch.object(dev_kit, "_WINDOWS", False), patch.object(dev_kit.shutil, "which") as which:
            self.assertEqual(dev_kit.resolve_executable_argv(["npm", "run", "build"]), ["npm", "run", "build"])
            which.assert_not_called()

    def test_missing_windows_executable_has_distinct_error(self):
        with patch.object(dev_kit, "_WINDOWS", True), patch.object(dev_kit.shutil, "which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "EXECUTABLE_NOT_FOUND.*definitely-missing-command"):
                dev_kit.resolve_executable_argv(["definitely-missing-command"])

    def test_focused_and_fresh_use_resolver_and_record_declared_argv(self):
        for phase in ("focused", "fresh"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                argv = ["npm", "run", "build", "a path & special"]
                inputs = {"checks": [{"name": "build", "category": "build", "argv": argv}]}
                with patch.object(dev_kit, "_load_run", return_value=(root, inputs)), patch.object(dev_kit, "_read_json", return_value={}), patch.object(dev_kit, "_save_lifecycle"), patch.object(dev_kit, "resolve_executable_argv", return_value=["resolved.CMD", *argv[1:]]) as resolve, patch.object(dev_kit.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "ok", "")) as run:
                    result = dev_kit.run_checks(root, phase)
                resolve.assert_called_once_with(argv)
                self.assertEqual(run.call_args.args[0], ["resolved.CMD", *argv[1:]])
                self.assertFalse(run.call_args.kwargs["shell"])
                self.assertEqual(result["checks"][0]["command"], argv)

    def test_missing_executable_fails_without_crashing_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = {"checks": [{"name": "build", "category": "build", "argv": ["definitely-missing-command"]}]}
            with patch.object(dev_kit, "_load_run", return_value=(root, inputs)), patch.object(dev_kit, "_WINDOWS", True), patch.object(dev_kit.shutil, "which", return_value=None):
                result = dev_kit.run_checks(root, "focused")
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("EXECUTABLE_NOT_FOUND", result["checks"][0]["stderr"])

    def test_fresh_install_loads_resolver_from_installed_runtime(self):
        from tooling import install_dev_kit

        source = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix="dev installed argv ") as directory:
            root = Path(directory)
            installed = install_dev_kit.install(source, root / "home")
            runtime = Path(installed["runtime_root"])
            script = "\n".join([
                "import json,sys",
                f"sys.path.insert(0, {str(runtime)!r})",
                "from tooling.lib import dev_kit",
                "from unittest.mock import patch",
                "with patch.object(dev_kit, '_WINDOWS', True), patch.object(dev_kit.shutil, 'which', return_value='resolved.CMD'):",
                " print(json.dumps({'module':dev_kit.__file__, 'argv':dev_kit.resolve_executable_argv(['npm','run','build','a path & special'])}))",
            ])
            proc = subprocess.run([sys.executable, "-I", "-c", script], cwd=root, capture_output=True, text=True, shell=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(Path(result["module"]), runtime / "tooling/lib/dev_kit.py")
            self.assertEqual(result["argv"], ["resolved.CMD", "run", "build", "a path & special"])
            self.assertEqual((runtime / "tooling/lib/dev_kit.py").read_bytes(), (source / "tooling/lib/dev_kit.py").read_bytes())

    @unittest.skipUnless(os.name == "nt" and shutil.which("npm"), "Windows npm required")
    def test_real_windows_npm_version_and_synthetic_build(self):
        with tempfile.TemporaryDirectory(prefix="dev argv space ") as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"scripts": {"build": 'node -e "process.exit(0)"'}}), encoding="utf-8")
            inputs = {"checks": [{"name": "npm version", "category": "build", "argv": ["npm", "--version"]}, {"name": "build", "category": "build", "argv": ["npm", "run", "build"]}]}
            with patch.object(dev_kit, "_load_run", return_value=(root, inputs)):
                result = dev_kit.run_checks(root, "focused")
            self.assertEqual(result["status"], "PASS", result)
