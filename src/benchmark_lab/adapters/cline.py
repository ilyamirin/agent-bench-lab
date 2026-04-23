from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class ClineAdapter(Adapter):
    name = "cline"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("cline") or "cline"

    def config_dir(self, home_dir: Path) -> Path:
        return home_dir / ".cline"

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
        if not Path(self.binary_path).exists():
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
                adapter_name=self.name,
                native_supported=False,
                details={"binary": self.binary_path, "reason": "cline CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "provider": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
            },
        )

    def prepare_workspace(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        config_dir = self.config_dir(home_dir)
        config_dir.mkdir(parents=True, exist_ok=True)
        return {"config_dir": str(config_dir)}

    def build_auth_command(self, run_spec: RunSpec, home_dir: Path, api_key: str) -> list[str]:
        return [
            self.binary_path,
            "auth",
            "--provider",
            "openrouter",
            "--apikey",
            api_key,
            "--modelid",
            run_spec.model,
            "--cwd",
            str(home_dir),
            "--config",
            str(self.config_dir(home_dir)),
        ]

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        home_dir = workspace_dir.parent / "home"
        app_root = self.app_root(workspace_dir)
        return [
            self.binary_path,
            "--yolo",
            "--json",
            "--model",
            run_spec.model,
            "--cwd",
            str(app_root),
            "--config",
            str(self.config_dir(home_dir)),
            "--timeout",
            str(run_spec.timeout_seconds),
            prompt,
        ]
