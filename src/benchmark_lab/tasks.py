from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TaskManifest:
    task_id: str
    title: str
    difficulty: str
    instructions: str
    acceptance_commands: list[str]
    expected_artifacts: list[str]
    timeout_seconds: int
    scoring_hooks: list[str]
    extra: dict[str, Any] = field(default_factory=dict)


def load_task_manifest(path: Path) -> TaskManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TaskManifest(
        task_id=payload["task_id"],
        title=payload["title"],
        difficulty=payload["difficulty"],
        instructions=payload["instructions"],
        acceptance_commands=payload["acceptance_commands"],
        expected_artifacts=payload["expected_artifacts"],
        timeout_seconds=payload["timeout_seconds"],
        scoring_hooks=payload["scoring_hooks"],
        extra=payload.get("extra", {}),
    )

