from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import Adapter
from ..browser_check import _resolve_playwright_wrapper
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class YulyaZigAdapter(Adapter):
    name = "yulya-zig"

    def __init__(self, repo_root: Path | None = None, zig_binary: str | None = None, built_binary: Path | None = None) -> None:
        root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
        self.repo_root = root
        self.zig_binary = zig_binary or shutil.which("zig") or "zig"
        self.built_binary = built_binary or (root / "native" / "yulya-zig" / "zig-out" / "bin" / "yulya-zig")

    def _version(self) -> str | None:
        binary = Path(self.built_binary)
        if not binary.exists():
            return None
        proc = subprocess.run(
            [str(binary), "version"],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        return (proc.stdout or proc.stderr).strip() or None

    def preflight(self, run_spec: RunSpec) -> CompatibilityResult:
        if run_spec.provider != "openrouter":
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_PROVIDER,
                adapter_name=self.name,
                native_supported=False,
                details={"provider": run_spec.provider},
            )
        if run_spec.model != "qwen/qwen3.6-plus":
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_MODEL,
                adapter_name=self.name,
                native_supported=False,
                details={"model": run_spec.model},
            )
        if not Path(self.zig_binary).exists():
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
                adapter_name=self.name,
                native_supported=False,
                details={"zig_binary": self.zig_binary, "reason": "zig not found"},
            )
        if not self.built_binary.exists():
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
                adapter_name=self.name,
                native_supported=False,
                details={"built_binary": str(self.built_binary), "reason": "yulya-zig binary not built"},
            )
        if shutil.which("docker") is None:
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_TRANSPORT,
                adapter_name=self.name,
                native_supported=False,
                details={"reason": "docker not found"},
            )
        try:
            wrapper = _resolve_playwright_wrapper()
        except FileNotFoundError as exc:
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
                adapter_name=self.name,
                native_supported=False,
                details={"reason": str(exc)},
            )
        details = {
            "zig_binary": self.zig_binary,
            "binary": str(self.built_binary),
            "browser_wrapper": str(wrapper),
            "provider": "openrouter",
            "model_ref": run_spec.model,
        }
        version = self._version()
        if version:
            details["version"] = version
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details=details,
        )

    def runtime_env(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path):
        env = dict(super().runtime_env(run_spec, workspace_dir, home_dir))
        env["OPENROUTER_API_KEY"] = "${OPENROUTER_API_KEY}"
        return env

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        return [
            str(self.built_binary),
            "run",
            "--workspace",
            str(self.app_root(workspace_dir)),
            "--run-root",
            str(run_spec.run_root),
            "--provider",
            run_spec.provider,
            "--model",
            run_spec.model,
            "--prompt",
            prompt,
            "--json",
        ]
