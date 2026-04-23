from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class OpenClawAdapter(Adapter):
    name = "openclaw"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("openclaw") or "openclaw"

    def invocation_model(self, run_spec: RunSpec) -> str:
        return f"openrouter/{run_spec.model}"

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
                details={"binary": self.binary_path, "reason": "openclaw CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "provider": "openrouter",
                "model_ref": self.invocation_model(run_spec),
                "execution_mode": "agent --local --json",
            },
        )

    def runtime_env(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        env = dict(super().runtime_env(run_spec, workspace_dir, home_dir))
        env.update(
            {
                "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
            }
        )
        return env

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def auth_commands(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
        api_key: str,
    ) -> list[list[str]]:
        app_root = self.app_root(workspace_dir)
        return [
            [
                self.binary_path,
                "onboard",
                "--non-interactive",
                "--accept-risk",
                "--mode",
                "local",
                "--auth-choice",
                "openrouter-api-key",
                "--openrouter-api-key",
                api_key,
                "--workspace",
                str(app_root),
                "--skip-health",
                "--skip-channels",
                "--skip-skills",
                "--skip-ui",
                "--skip-search",
                "--no-install-daemon",
            ],
            [
                self.binary_path,
                "models",
                "set",
                self.invocation_model(run_spec),
            ],
        ]

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = workspace_dir
        return [
            self.binary_path,
            "agent",
            "--local",
            "--agent",
            "main",
            "--thinking",
            "off",
            "--timeout",
            str(run_spec.timeout_seconds),
            "--message",
            prompt,
            "--json",
        ]
