from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Mapping

from ..models import CompatibilityResult, RunSpec


class Adapter(ABC):
    name: str

    @abstractmethod
    def preflight(self, run_spec: RunSpec) -> CompatibilityResult:
        raise NotImplementedError

    def auth_commands(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
        api_key: str,
    ) -> list[list[str]]:
        _ = (run_spec, workspace_dir, home_dir, api_key)
        return []

    def prepare_workspace(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
    ) -> dict[str, str]:
        _ = (run_spec, workspace_dir, home_dir)
        return {}

    def runtime_env(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
    ) -> Mapping[str, str]:
        _ = (run_spec, workspace_dir)
        return {
            "HOME": str(home_dir),
            "XDG_CONFIG_HOME": str(home_dir / ".config"),
            "XDG_DATA_HOME": str(home_dir / ".local" / "share"),
            "XDG_STATE_HOME": str(home_dir / ".local" / "state"),
            "XDG_CACHE_HOME": str(home_dir / ".cache"),
        }

    def app_root(self, workspace_dir: Path) -> Path:
        return workspace_dir / "upstream" / "mediacms"

    def command_cwd(self, workspace_dir: Path) -> Path:
        return workspace_dir

    def git_repo_root(self, workspace_dir: Path) -> Path:
        return workspace_dir

    def auth_cwd(self, workspace_dir: Path, home_dir: Path) -> Path:
        _ = home_dir
        return self.command_cwd(workspace_dir)

    def finalize_run(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
        home_dir: Path,
        env: Mapping[str, str],
        stdout_path: Path,
        stderr_path: Path,
    ) -> dict[str, str]:
        _ = (run_spec, workspace_dir, home_dir, env, stdout_path, stderr_path)
        return {}

    @abstractmethod
    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        raise NotImplementedError
