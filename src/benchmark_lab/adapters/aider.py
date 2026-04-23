from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class AiderAdapter(Adapter):
    name = "aider"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("aider") or "aider"

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
                details={"binary": self.binary_path, "reason": "aider CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "api_base": "https://openrouter.ai/api/v1",
                "model_arg": self.invocation_model(run_spec),
            },
        )

    def runtime_env(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        env = dict(super().runtime_env(run_spec, workspace_dir, home_dir))
        env.update(
            {
                "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
                "OPENAI_API_KEY": "${OPENROUTER_API_KEY}",
                "AIDER_OPENAI_API_KEY": "${OPENROUTER_API_KEY}",
                "AIDER_OPENAI_API_BASE": "https://openrouter.ai/api/v1",
                "AIDER_MODEL": run_spec.model,
                "AIDER_ANALYTICS": "false",
                "AIDER_INPUT_HISTORY_FILE": str(workspace_dir / ".aider.input.history"),
                "AIDER_CHAT_HISTORY_FILE": str(workspace_dir / ".aider.chat.history.md"),
                "AIDER_LLM_HISTORY_FILE": str(workspace_dir / ".aider.llm.history.jsonl"),
            }
        )
        return env

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = workspace_dir
        command = [
            self.binary_path,
            "--model",
            self.invocation_model(run_spec),
            "--yes-always",
            "--message",
            prompt,
            "--exit",
            "--no-show-model-warnings",
            "--no-check-update",
            "--analytics-disable",
            "--no-auto-commits",
            "--no-dirty-commits",
            "--subtree-only",
        ]
        # File seeding keeps Aider focused on the MediaCMS slice under evaluation instead of the harness repo.
        for path in (
            "files/models/media.py",
            "files/serializers.py",
            "files/forms.py",
            "files/admin.py",
            "files/tests/test_content_warning.py",
            "files/migrations/0015_media_content_warning.py",
        ):
            command.extend(["--file", path])
        for path in (
            "tests/api/test_new_media.py",
            "files/tests/user_utils.py",
            "manage.py",
        ):
            command.extend(["--read", path])
        return command
