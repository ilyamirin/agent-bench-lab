from __future__ import annotations

import unittest
from pathlib import Path

from benchmark_lab.docker_env import MediaCMSBaseline


class DockerBaselineTest(unittest.TestCase):
    def test_baseline_points_at_upstream_dev_compose_and_overlay(self) -> None:
        baseline = MediaCMSBaseline(repo_root=Path.cwd())

        compose_files = baseline.compose_files()

        self.assertEqual(
            compose_files[0],
            Path.cwd() / "upstream" / "mediacms" / "docker-compose-dev.yaml",
        )
        self.assertEqual(
            compose_files[1],
            Path.cwd() / "docker" / "compose.benchmark.yaml",
        )
        self.assertEqual(baseline.role_to_service["app"], "web")
        self.assertEqual(baseline.role_to_service["db"], "db")
        self.assertEqual(baseline.role_to_service["worker"], "celery_worker")
        self.assertEqual(baseline.role_to_service["runner"], "benchmark_runner")
        self.assertEqual(baseline.role_to_service["judge"], "benchmark_judge")


if __name__ == "__main__":
    unittest.main()
