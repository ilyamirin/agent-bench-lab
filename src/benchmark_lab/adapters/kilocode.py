from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from subprocess import run

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class KiloCodeAdapter(Adapter):
    name = "kilocode"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("kilocode") or shutil.which("kilo") or "kilo"

    def config_root(self, home_dir: Path) -> Path:
        return home_dir / ".config" / "kilo"

    def auth_path(self, home_dir: Path) -> Path:
        return home_dir / ".local" / "share" / "kilo" / "auth.json"

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
                details={"binary": self.binary_path, "reason": "kilo CLI not found"},
            )
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details={
                "binary": self.binary_path,
                "provider_config": "kilo.json + auth.json",
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
        (config_root / "kilo.json").write_text(
            json.dumps(
                {
                    "$schema": "https://app.kilo.ai/config.json",
                    "enabled_providers": ["openrouter"],
                    "model": f"openrouter/{run_spec.model}",
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return {"config_root": str(config_root), "auth_path": str(auth_path)}

    def runtime_env(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
    ) -> dict[str, str]:
        env = dict(super().runtime_env(run_spec, workspace_dir, home_dir))
        env["OPENROUTER_API_KEY"] = "${OPENROUTER_API_KEY}"
        return env

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        app_root = self.app_root(workspace_dir)
        return [
            self.binary_path,
            "run",
            "--auto",
            "--format",
            "json",
            "--model",
            f"openrouter/{run_spec.model}",
            "--dir",
            str(app_root),
            prompt,
        ]

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def finalize_run(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
        env: dict[str, str],
        stdout_path: Path,
        stderr_path: Path,
    ) -> dict[str, str]:
        _ = stderr_path
        session_id = ""
        for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = payload.get("sessionID") or session_id
        if not session_id:
            return {}

        export_path = run_spec.run_root / "kilo-export.json"
        metadata_path = run_spec.run_root / "kilo-session.json"
        export_proc = run(
            [self.binary_path, "export", session_id],
            cwd=self.command_cwd(workspace_dir),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        export_path.write_text(export_proc.stdout or "", encoding="utf-8")
        metadata_path.write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "export_command": [self.binary_path, "export", session_id],
                    "export_returncode": export_proc.returncode,
                    "export_stderr": export_proc.stderr,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return {
            "session_id": session_id,
            "kilo_export_path": str(export_path),
            "kilo_session_path": str(metadata_path),
        }
