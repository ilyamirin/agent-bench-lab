from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmark_lab.models import CompatibilityResult, CompatibilityStatus, RunResult, RunSpec, RunStatus, ScoreCard
from benchmark_lab.single_run import main


class SingleRunCliTest(unittest.TestCase):
    def test_single_run_invokes_runner_once_and_prints_result(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="benchmark-single-run-"))
        run_spec = RunSpec(
            agent_id="cline",
            task_id="simple_content_warning",
            attempt=10,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=temp_dir,
        )
        fake_result = RunResult(
            run_spec=run_spec,
            compatibility=CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                adapter_name="cline",
                native_supported=True,
            ),
            status=RunStatus.SUCCESS,
            exit_code=0,
            duration_seconds=12.0,
            stdout_path=temp_dir / "stdout.log",
            stderr_path=temp_dir / "stderr.log",
            patch_path=temp_dir / "changes.patch",
            scores=ScoreCard(task_solved=4, reliability=None, quality=None, speed_cost=3, pending_axes=[]),
            automated_checks=[],
            manual_review={"status": "pending"},
            actual_provider="openrouter",
            actual_model="qwen/qwen3.6-plus",
        )

        with (
            patch("benchmark_lab.single_run.BenchmarkRunner") as mocked_runner_cls,
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            mocked_runner = mocked_runner_cls.return_value
            mocked_runner.load_task.return_value.timeout_seconds = 900
            mocked_runner.workspace_snapshot_ref.return_value = "mediacms@deadbeef"
            mocked_runner.run_attempt.return_value = fake_result

            exit_code = main(
                [
                    "--repo-root",
                    str(temp_dir),
                    "--agent",
                    "cline",
                    "--attempt",
                    "10",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["run_id"], "cline__simple_content_warning__attempt-10")
        mocked_runner.run_attempt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
