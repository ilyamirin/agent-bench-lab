from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmark_lab.models import RunStatus, RunSpec
from benchmark_lab.runner import BenchmarkRunner


class RunnerDockerPreflightTest(unittest.TestCase):
    def test_docker_preflight_returns_infra_error_result(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="benchmark-runner-"))
        runner = BenchmarkRunner(temp_dir)
        run_spec = RunSpec(
            agent_id="aider",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=temp_dir,
        )
        paths = runner._result_paths(run_spec)

        with patch("benchmark_lab.runner.subprocess.run") as mocked_run:
            mocked_run.return_value.returncode = 1
            mocked_run.return_value.stdout = ""
            mocked_run.return_value.stderr = "permission denied"

            result = runner._docker_preflight(run_spec, paths)

        assert result is not None
        self.assertEqual(result.status, RunStatus.INFRA_ERROR)
        self.assertEqual(result.automated_checks[0]["name"], "docker_preflight")
        artifact_path = Path(result.automated_checks[0]["artifact"])
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["stderr"], "permission denied")


class RunnerBrowserSeedTimeoutTest(unittest.TestCase):
    def test_seed_browser_media_times_out_cleanly(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="benchmark-runner-"))
        runner = BenchmarkRunner(temp_dir)
        run_spec = RunSpec(
            agent_id="pi",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=temp_dir,
        )
        workspace_dir = temp_dir / "workspace"
        (workspace_dir / "upstream" / "mediacms").mkdir(parents=True, exist_ok=True)

        with patch("benchmark_lab.runner.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["docker"], timeout=60)):
            seeded, media_id, error_text = runner._seed_browser_media(run_spec, workspace_dir)

        self.assertFalse(seeded)
        self.assertIsNone(media_id)
        self.assertIn("Timed out after", error_text)


if __name__ == "__main__":
    unittest.main()
