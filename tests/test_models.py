from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmark_lab.models import (
    CompatibilityResult,
    CompatibilityStatus,
    RunResult,
    RunSpec,
    RunStatus,
    ScoreCard,
)


class ModelsTest(unittest.TestCase):
    def test_run_result_serializes_enums_and_paths(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="benchmark-models-"))
        run_spec = RunSpec(
            agent_id="qwen-code",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=temp_dir,
        )
        result = RunResult(
            run_spec=run_spec,
            compatibility=CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                adapter_name="qwen-code",
                native_supported=True,
                details={"binary": "/opt/homebrew/bin/qwen"},
            ),
            status=RunStatus.SUCCESS,
            exit_code=0,
            duration_seconds=12.5,
            stdout_path=temp_dir / "stdout.log",
            stderr_path=temp_dir / "stderr.log",
            patch_path=temp_dir / "changes.patch",
            scores=ScoreCard(
                task_solved=4,
                reliability=None,
                quality=None,
                speed_cost=3,
                pending_axes=["reliability", "quality"],
            ),
            automated_checks=[
                {"name": "environment_boot", "passed": True},
                {"name": "targeted_tests", "passed": True},
            ],
            manual_review={"status": "pending"},
            actual_provider="openrouter",
            actual_model="qwen/qwen3.6-plus",
        )

        payload = result.to_dict()

        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["compatibility"]["status"], "compatible")
        self.assertEqual(payload["scores"]["task_solved"], 4)
        self.assertEqual(payload["scores"]["pending_axes"], ["reliability", "quality"])
        self.assertTrue(payload["stdout_path"].endswith("stdout.log"))
        json.dumps(payload)

    def test_run_spec_builds_stable_run_id(self) -> None:
        run_spec = RunSpec(
            agent_id="qwen-code",
            task_id="simple_content_warning",
            attempt=3,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=Path("/tmp/benchmark-root"),
        )

        self.assertEqual(run_spec.run_id, "qwen-code__simple_content_warning__attempt-3")


if __name__ == "__main__":
    unittest.main()
