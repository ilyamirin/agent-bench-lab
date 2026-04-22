from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MediaCMSBaseline:
    repo_root: Path
    role_to_service: dict[str, str] = field(
        default_factory=lambda: {
            "app": "web",
            "db": "db",
            "worker": "celery_worker",
            "runner": "benchmark_runner",
            "judge": "benchmark_judge",
        }
    )

    def compose_files(self) -> list[Path]:
        return [
            self.repo_root / "upstream" / "mediacms" / "docker-compose-dev.yaml",
            self.repo_root / "docker" / "compose.benchmark.yaml",
        ]

