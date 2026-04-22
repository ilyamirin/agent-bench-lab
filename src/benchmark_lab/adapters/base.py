from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import CompatibilityResult, RunSpec


class Adapter(ABC):
    name: str

    @abstractmethod
    def preflight(self, run_spec: RunSpec) -> CompatibilityResult:
        raise NotImplementedError

    @abstractmethod
    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: str) -> list[str]:
        raise NotImplementedError

