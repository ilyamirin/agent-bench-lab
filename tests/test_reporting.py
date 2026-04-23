from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmark_lab.models import CompatibilityResult, CompatibilityStatus, RunResult, RunSpec, RunStatus, ScoreCard
from benchmark_lab.reporting import (
    render_cohort_summary,
    render_markdown_summary,
    render_radar_chart_svg,
    write_preflight_json,
    write_run_result_json,
)


class ReportingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="benchmark-reporting-"))
        self.run_spec = RunSpec(
            agent_id="qwen-code",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=self.temp_dir,
        )
        self.run_result = RunResult(
            run_spec=self.run_spec,
            compatibility=CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                adapter_name="qwen-code",
                native_supported=True,
            ),
            status=RunStatus.SUCCESS,
            exit_code=0,
            duration_seconds=42.0,
            stdout_path=self.temp_dir / "stdout.log",
            stderr_path=self.temp_dir / "stderr.log",
            patch_path=self.temp_dir / "changes.patch",
            scores=ScoreCard(
                task_solved=4,
                reliability=None,
                quality=None,
                speed_cost=3,
                pending_axes=["reliability", "quality"],
            ),
            automated_checks=[{"name": "environment_boot", "passed": True}],
            manual_review={"status": "pending"},
            actual_provider="openrouter",
            actual_model="qwen/qwen3.6-plus",
        )

    def test_json_writer_persists_normalized_result(self) -> None:
        output_path = self.temp_dir / "result.json"

        write_run_result_json(self.run_result, output_path)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["actual_model"], "qwen/qwen3.6-plus")

    def test_markdown_summary_and_radar_chart_include_pending_axes(self) -> None:
        markdown = render_markdown_summary([self.run_result])
        svg = render_radar_chart_svg("Qwen Code", self.run_result.scores)

        self.assertIn("qwen-code", markdown)
        self.assertIn("pending", markdown)
        self.assertIn("<svg", svg)
        self.assertIn("task solved", svg)
        self.assertIn("reliability", svg)

    def test_cohort_summary_and_preflight_writer(self) -> None:
        incompatible = RunResult(
            run_spec=RunSpec(
                agent_id="codebuff",
                task_id="simple_content_warning",
                attempt=1,
                provider="openrouter",
                model="qwen/qwen3.6-plus",
                workspace_snapshot_ref="mediacms@deadbeef",
                timeout_seconds=900,
                repo_root=self.temp_dir,
            ),
            compatibility=CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE_UNKNOWN,
                adapter_name="codebuff",
                native_supported=False,
                details={"reason": "native CLI not found"},
            ),
            status=RunStatus.INCOMPATIBLE,
            exit_code=None,
            duration_seconds=None,
            stdout_path=None,
            stderr_path=None,
            patch_path=None,
            scores=ScoreCard(task_solved=0, reliability=None, quality=None, speed_cost=None, pending_axes=[]),
            automated_checks=[],
            manual_review={"status": "pending"},
            actual_provider="openrouter",
            actual_model="qwen/qwen3.6-plus",
        )

        markdown = render_cohort_summary([self.run_result], [incompatible])
        preflight_path = self.temp_dir / "preflight.json"
        write_preflight_json("compatible", {"adapter_name": "qwen-code"}, preflight_path)

        self.assertIn("Executed Agents", markdown)
        self.assertIn("Incompatible Agents", markdown)
        self.assertTrue(preflight_path.exists())


if __name__ == "__main__":
    unittest.main()
