from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class HermesAdapter(Adapter):
    name = "hermes-agent"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("hermes") or "hermes"

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
                details={"binary": self.binary_path, "reason": "hermes CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "provider": "openrouter",
                "model_arg": run_spec.model,
                "state_root": "HERMES_HOME",
            },
        )

    def runtime_env(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        env = dict(super().runtime_env(run_spec, workspace_dir, home_dir))
        env.update(
            {
                "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
                "HERMES_HOME": str(home_dir / ".hermes"),
                "HERMES_ACCEPT_HOOKS": "1",
            }
        )
        return env

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = workspace_dir
        return [
            self.binary_path,
            "chat",
            "-q",
            prompt,
            "--provider",
            "openrouter",
            "--model",
            run_spec.model,
            "--quiet",
            "--yolo",
            "--source",
            "tool",
            "--max-turns",
            "90",
        ]
