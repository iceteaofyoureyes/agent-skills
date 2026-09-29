"""Portable Codex CLI resolution for Test Kit native invocations."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CODEX_COMMAND_ENV = "TEST_KIT_CODEX_COMMAND"
_NPM_CODEX_ENTRYPOINT = re.compile(
    r"node_modules[\\/]+@openai[\\/]+codex[\\/]+bin[\\/]+codex\.js", re.IGNORECASE,
)


class CodexDependencyError(RuntimeError):
    def __init__(self, message: str, *, code: str = "CODEX_MISSING_DEPENDENCY"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CodexCommand:
    argv_prefix: tuple[str, ...]
    target: str
    resolution: str

    def argv(self, arguments: Iterable[str]) -> list[str]:
        return [*self.argv_prefix, *(os.fspath(argument) for argument in arguments)]


def _dependency_message() -> str:
    return (
        "Codex CLI is required for native Test Kit invocation. Make `codex` available on PATH "
        f"or configure {CODEX_COMMAND_ENV} with a Codex executable or codex.js path."
    )


def _node_command(script: Path, *, launcher: Path | None = None, resolution: str) -> CodexCommand:
    node = launcher.parent / "node.exe" if launcher is not None and os.name == "nt" else None
    node = node if node is not None and node.is_file() else None
    node = node or shutil.which("node.exe" if os.name == "nt" else "node") or shutil.which("node")
    if node is None:
        raise CodexDependencyError(
            "The resolved Codex JavaScript entrypoint requires Node.js on PATH.",
            code="CODEX_NODE_MISSING_DEPENDENCY",
        )
    return CodexCommand((str(node), str(script.resolve())), str(script.resolve()), resolution)


def _npm_entrypoint(launcher: Path) -> Path | None:
    try:
        wrapper = launcher.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not _NPM_CODEX_ENTRYPOINT.search(wrapper):
        return None
    script = launcher.parent / "node_modules/@openai/codex/bin/codex.js"
    return script if script.is_file() else None


def _from_path(path: str | Path, *, resolution: str) -> CodexCommand:
    launcher = Path(path).expanduser().resolve()
    if not launcher.is_file():
        raise CodexDependencyError(
            f"Resolved Codex command is not a file: {path}", code="CODEX_INVALID_OVERRIDE",
        )
    suffix = launcher.suffix.casefold()
    if suffix == ".js":
        return _node_command(launcher, resolution=resolution)
    if suffix in {".cmd", ".ps1"}:
        script = _npm_entrypoint(launcher)
        if script is not None:
            return _node_command(script, launcher=launcher, resolution=resolution)
        raise CodexDependencyError(
            f"The resolved {suffix} file is not the standard Codex npm shim; configure "
            f"{CODEX_COMMAND_ENV} with codex.exe or codex.js.",
            code="CODEX_UNSUPPORTED_COMMAND",
        )
    if suffix == ".bat":
        raise CodexDependencyError(
            "A generic .bat Codex launcher cannot be invoked with safe argument boundaries; "
            f"configure {CODEX_COMMAND_ENV} with codex.exe, a Codex PowerShell launcher, or codex.js.",
            code="CODEX_UNSUPPORTED_COMMAND",
        )
    if os.name == "nt" and suffix not in {".exe", ".com", ""}:
        raise CodexDependencyError(
            f"Unsupported Codex launcher form: {launcher.suffix}", code="CODEX_UNSUPPORTED_COMMAND",
        )
    if os.name != "nt" and not os.access(launcher, os.X_OK):
        raise CodexDependencyError(
            f"Codex command is not executable: {launcher}", code="CODEX_INVALID_OVERRIDE",
        )
    return CodexCommand((str(launcher),), str(launcher), resolution)


def _find_path_launcher() -> str | None:
    if os.name != "nt":
        return shutil.which("codex")

    # Prefer a native executable, then the PATH command (including the npm .cmd shim).
    launcher = shutil.which("codex.exe") or shutil.which("codex") or shutil.which("codex.cmd")
    if launcher:
        return launcher
    launcher = shutil.which("codex.ps1")
    if launcher:
        return launcher
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if directory:
            candidate = Path(directory.strip('"')) / "codex.ps1"
            if candidate.is_file():
                return str(candidate)
    return None


def resolve_codex_command() -> CodexCommand:
    """Resolve a safe argv prefix from an explicit override or PATH."""
    override = os.environ.get(CODEX_COMMAND_ENV, "").strip()
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return _from_path(candidate, resolution=CODEX_COMMAND_ENV)
        if "/" not in override and "\\" not in override:
            found = shutil.which(override)
            if found:
                return _from_path(found, resolution=CODEX_COMMAND_ENV)
        raise CodexDependencyError(
            f"{CODEX_COMMAND_ENV} does not identify an available Codex command: {override}. "
            "The explicit override is authoritative; PATH fallback was not attempted.",
            code="CODEX_INVALID_OVERRIDE",
        )

    launcher = _find_path_launcher()
    if launcher:
        return _from_path(launcher, resolution="PATH")
    raise CodexDependencyError(_dependency_message())
