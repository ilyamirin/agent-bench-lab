from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class OpenHandsAdapter(Adapter):
    name = "openhands"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("openhands") or "openhands"

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
                details={"binary": self.binary_path, "reason": "openhands CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "env_override": ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"],
            },
        )

    def runtime_env(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        env = dict(super().runtime_env(run_spec, workspace_dir, home_dir))
        env.update(
            {
                "LLM_API_KEY": "${OPENROUTER_API_KEY}",
                "LLM_BASE_URL": "https://openrouter.ai/api/v1",
                "LLM_MODEL": run_spec.model,
            }
        )
        return env

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = (run_spec, workspace_dir)
        return [
            self.binary_path,
            "--headless",
            "--json",
            "--always-approve",
            "--override-with-envs",
            "--task",
            prompt,
        ]
