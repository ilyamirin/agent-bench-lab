from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class RunStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INCOMPATIBLE = "incompatible"
    INFRA_ERROR = "infra_error"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE_PROVIDER = "incompatible_provider"
    INCOMPATIBLE_MODEL = "incompatible_model"
    INCOMPATIBLE_TRANSPORT = "incompatible_transport"
    INCOMPATIBLE_UNKNOWN = "incompatible_unknown"


@dataclass(slots=True)
class ScoreCard:
    task_solved: int | None
    reliability: int | None
    quality: int | None
    speed_cost: int | None
    pending_axes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_solved": self.task_solved,
            "reliability": self.reliability,
            "quality": self.quality,
            "speed_cost": self.speed_cost,
            "pending_axes": list(self.pending_axes),
        }


@dataclass(slots=True)
class CompatibilityResult:
    status: CompatibilityStatus
    adapter_name: str
    native_supported: bool
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "adapter_name": self.adapter_name,
            "native_supported": self.native_supported,
            "details": self.details,
        }


@dataclass(slots=True)
class RunSpec:
    agent_id: str
    task_id: str
    attempt: int
    provider: str
    model: str
    workspace_snapshot_ref: str
    timeout_seconds: int
    repo_root: Path

    @property
    def run_id(self) -> str:
        return f"{self.agent_id}__{self.task_id}__attempt-{self.attempt}"

    @property
    def run_root(self) -> Path:
        return self.repo_root / "runs" / self.run_id

    @property
    def web_port(self) -> int:
        # Use a deterministic high port so concurrent benchmark runs do not contend for :80.
        digest = hashlib.sha1(self.run_id.encode("utf-8")).hexdigest()
        return 15000 + (int(digest[:6], 16) % 10000)


@dataclass(slots=True)
class RunResult:
    run_spec: RunSpec
    compatibility: CompatibilityResult
    status: RunStatus
    exit_code: int | None
    duration_seconds: float | None
    stdout_path: Path | None
    stderr_path: Path | None
    patch_path: Path | None
    scores: ScoreCard
    automated_checks: list[dict[str, Any]]
    manual_review: dict[str, Any]
    actual_provider: str | None
    actual_model: str | None
    run_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_spec.run_id,
            "run_spec": {
                "agent_id": self.run_spec.agent_id,
                "task_id": self.run_spec.task_id,
                "attempt": self.run_spec.attempt,
                "provider": self.run_spec.provider,
                "model": self.run_spec.model,
                "workspace_snapshot_ref": self.run_spec.workspace_snapshot_ref,
                "timeout_seconds": self.run_spec.timeout_seconds,
            },
            "compatibility": self.compatibility.to_dict(),
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "stdout_path": str(self.stdout_path) if self.stdout_path else None,
            "stderr_path": str(self.stderr_path) if self.stderr_path else None,
            "patch_path": str(self.patch_path) if self.patch_path else None,
            "scores": self.scores.to_dict(),
            "automated_checks": self.automated_checks,
            "manual_review": self.manual_review,
            "actual_provider": self.actual_provider,
            "actual_model": self.actual_model,
            "run_metadata": self.run_metadata,
        }
