from __future__ import annotations

import json
from pathlib import Path

from .adapters.qwen_code import QwenCodeAdapter
from .models import RunResult, RunSpec, RunStatus, ScoreCard
from .reporting import write_run_result_json
from .workspace import create_workspace_snapshot


class BenchmarkRunner:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def prepare_workspace(self, run_spec: RunSpec) -> Path:
        return create_workspace_snapshot(self.repo_root, run_spec.run_root / "workspace")

    def write_qwen_settings(self, run_spec: RunSpec, workspace_dir: Path) -> Path:
        adapter = QwenCodeAdapter()
        settings = adapter.build_settings(run_spec)
        settings_path = adapter.settings_path(workspace_dir)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")
        return settings_path

    def persist_stub_result(self, run_result: RunResult) -> Path:
        output_path = run_result.run_spec.run_root / "result.json"
        write_run_result_json(run_result, output_path)
        return output_path

    def build_incompatible_result(self, run_spec: RunSpec, reason_status, details: dict | None = None) -> RunResult:
        from .models import CompatibilityResult

        return RunResult(
            run_spec=run_spec,
            compatibility=CompatibilityResult(
                status=reason_status,
                adapter_name="qwen-code",
                native_supported=False,
                details=details or {},
            ),
            status=RunStatus.INCOMPATIBLE,
            exit_code=None,
            duration_seconds=None,
            stdout_path=None,
            stderr_path=None,
            patch_path=None,
            scores=ScoreCard(
                task_solved=0,
                reliability=None,
                quality=None,
                speed_cost=None,
                pending_axes=["reliability", "quality", "speed/cost"],
            ),
            automated_checks=[],
            manual_review={"status": "pending"},
            actual_provider=run_spec.provider,
            actual_model=run_spec.model,
        )

