from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class OpenCodeAdapter(Adapter):
    name = "opencode"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("opencode") or "opencode"

    def config_root(self, home_dir: Path) -> Path:
        return home_dir / ".config" / "opencode"

    def auth_path(self, home_dir: Path) -> Path:
        return home_dir / ".local" / "share" / "opencode" / "auth.json"

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
                details={"binary": self.binary_path, "reason": "opencode CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "provider_config": "opencode.json + auth.json",
                "invocation_model": f"openrouter/{run_spec.model}",
            },
        )

    def prepare_workspace(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        config_root = self.config_root(home_dir)
        config_root.mkdir(parents=True, exist_ok=True)
        auth_path = self.auth_path(home_dir)
        auth_path.parent.mkdir(parents=True, exist_ok=True)
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        auth_path.write_text(
            json.dumps({"openrouter": {"type": "api", "key": api_key}}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (config_root / "opencode.json").write_text(
            json.dumps(
                {
                    "$schema": "https://opencode.ai/config.json",
                    "enabled_providers": ["openrouter"],
                    "model": f"openrouter/{run_spec.model}",
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return {"config_root": str(config_root), "auth_path": str(auth_path)}

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        return [
            self.binary_path,
            "run",
            "--format",
            "json",
            "--dangerously-skip-permissions",
            "--model",
            f"openrouter/{run_spec.model}",
            "--dir",
            str(workspace_dir),
            prompt,
        ]
