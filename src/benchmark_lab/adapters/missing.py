from __future__ import annotations

import shutil
from pathlib import Path

from .base import Adapter
from ..models import CompatibilityResult, CompatibilityStatus, RunSpec


class MissingBinaryAdapter(Adapter):
    def __init__(
        self,
        name: str,
        binary_candidates: list[str],
        *,
        missing_status: CompatibilityStatus = CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
        missing_reason: str = "native CLI not found in current environment",
        implemented_status: CompatibilityStatus = CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
        implemented_reason: str = "binary exists but native headless adapter is not implemented",
        extra_details: dict | None = None,
    ) -> None:
        self.name = name
        self.binary_candidates = binary_candidates
        self.missing_status = missing_status
        self.missing_reason = missing_reason
        self.implemented_status = implemented_status
        self.implemented_reason = implemented_reason
        self.extra_details = extra_details or {}
        self.binary_path = next((shutil.which(candidate) for candidate in binary_candidates if shutil.which(candidate)), None)

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
        if self.binary_path and Path(self.binary_path).exists():
            return CompatibilityResult(
                status=self.implemented_status,
                adapter_name=self.name,
                native_supported=False,
                details={
                    "binary": self.binary_path,
                    "reason": self.implemented_reason,
                    **self.extra_details,
                },
            )
        return CompatibilityResult(
            status=self.missing_status,
            adapter_name=self.name,
            native_supported=False,
            details={
                "binary_candidates": self.binary_candidates,
                "reason": self.missing_reason,
                **self.extra_details,
            },
        )

    def build_command(self, run_spec: RunSpec, prompt: str, workspace_dir: Path) -> list[str]:
        _ = (run_spec, prompt, workspace_dir)
        raise RuntimeError(f"{self.name} is not runnable")
