from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class QwenCodeAdapter(Adapter):
    name = "qwen-code"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("qwen") or "qwen"

    def build_settings(self, run_spec: RunSpec) -> dict:
        return {
            "modelProviders": {
                "openai": [
                    {
                        "id": run_spec.model,
                        "name": run_spec.model,
                        "envKey": "OPENROUTER_API_KEY",
                        "baseUrl": "https://openrouter.ai/api/v1",
                        "description": "Benchmark policy model via OpenRouter",
                    }
                ]
            },
            "security": {
                "auth": {
                    "selectedType": "openai",
                }
            },
            "model": {
                "name": run_spec.model,
            },
        }

    def settings_path(self, workspace_dir: Path) -> Path:
        return workspace_dir / ".qwen" / "settings.json"

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
                details={"binary": self.binary_path, "reason": "qwen CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={"binary": self.binary_path, "auth_type": "openai"},
        )

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = workspace_dir
        return [
            self.binary_path,
            "--auth-type",
            "openai",
            "--model",
            run_spec.model,
            "--output-format",
            "json",
            "--yolo",
            "--prompt",
            prompt,
        ]

