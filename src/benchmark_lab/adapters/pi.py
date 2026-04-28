from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from shlex import quote

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class PiAdapter(Adapter):
    name = "pi"

    def __init__(self, binary_path: str | None = None) -> None:
        self.binary_path = binary_path or shutil.which("pi") or "pi"

    def pi_root(self, home_dir: Path) -> Path:
        return home_dir / ".pi" / "agent"

    def auth_path(self, home_dir: Path) -> Path:
        return self.pi_root(home_dir) / "auth.json"

    def settings_path(self, home_dir: Path) -> Path:
        return self.pi_root(home_dir) / "settings.json"

    def session_dir(self, home_dir: Path) -> Path:
        return self.pi_root(home_dir) / "sessions"

    def _resolved_version(self) -> str | None:
        binary = Path(self.binary_path)
        if not binary.exists():
            return None
        proc = subprocess.run(
            [self.binary_path, "--version"],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        version = (proc.stdout or proc.stderr).strip()
        return version or None

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
                details={"binary": self.binary_path, "reason": "pi CLI not found"},
            )
        details = {
            "binary": self.binary_path,
            "provider": "openrouter",
            "model_ref": f"openrouter/{run_spec.model}",
            "execution_mode": "pi --mode json --provider openrouter --model qwen/qwen3.6-plus -p",
        }
        version = self._resolved_version()
        if version:
            details["version"] = version
        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=self.name,
            native_supported=True,
            details=details,
        )

    def prepare_workspace(self, run_spec: RunSpec, workspace_dir: Path, home_dir: Path) -> dict[str, str]:
        _ = (run_spec, workspace_dir)
        self.pi_root(home_dir).mkdir(parents=True, exist_ok=True)
        self.session_dir(home_dir).mkdir(parents=True, exist_ok=True)
        return {
            "pi_root": str(self.pi_root(home_dir)),
            "auth_path": str(self.auth_path(home_dir)),
            "settings_path": str(self.settings_path(home_dir)),
            "session_dir": str(self.session_dir(home_dir)),
        }

    def auth_commands(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
        api_key: str,
    ) -> list[list[str]]:
        _ = (workspace_dir,)
        auth_payload = {
            "openrouter": {
                "type": "api_key",
                "key": api_key,
            }
        }
        settings_payload = {
            "defaultProvider": "openrouter",
            "defaultModel": run_spec.model,
            "quietStartup": True,
            "sessionDir": str(self.session_dir(home_dir)),
        }
        auth_command = (
            f"mkdir -p {quote(str(self.pi_root(home_dir)))} && "
            f"cat > {quote(str(self.auth_path(home_dir)))} <<'EOF'\n"
            f"{json.dumps(auth_payload, indent=2, sort_keys=True)}\nEOF\n"
            f"chmod 600 {quote(str(self.auth_path(home_dir)))}\n"
        )
        settings_command = (
            f"mkdir -p {quote(str(self.pi_root(home_dir)))} && "
            f"cat > {quote(str(self.settings_path(home_dir)))} <<'EOF'\n"
            f"{json.dumps(settings_payload, indent=2, sort_keys=True)}\nEOF\n"
            f"chmod 600 {quote(str(self.settings_path(home_dir)))}\n"
        )
        return [["sh", "-lc", auth_command], ["sh", "-lc", settings_command]]

    def command_cwd(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return self.app_root(workspace_dir)

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = run_spec
        return [
            self.binary_path,
            "--mode",
            "json",
            "--provider",
            "openrouter",
            "--model",
            run_spec.model,
            "-p",
            prompt,
        ]
