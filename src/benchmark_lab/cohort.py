from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import RunResult, RunSpec
from .runner import BenchmarkRunner


DEFAULT_AGENT_IDS = [
    "aider",
    "cline",
    "opencode",
    "kilocode",
    "openhands",
    "codebuff",
    "crush",
    "hermes-agent",
    "openclaw",
]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run cohort benchmark for task 1")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--task-id", default="simple_content_warning")
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--model", default="qwen/qwen3.6-plus")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--start-at", type=int, default=1)
    parser.add_argument("--agents", nargs="*", default=DEFAULT_AGENT_IDS)
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    runner = BenchmarkRunner(repo_root)
    task = runner.load_task(args.task_id)
    snapshot_ref = runner.workspace_snapshot_ref()
    results: list[RunResult] = []

    for agent_id in args.agents:
        for attempt in range(args.start_at, args.start_at + args.attempts):
            run_spec = RunSpec(
                agent_id=agent_id,
                task_id=args.task_id,
                attempt=attempt,
                provider=args.provider,
                model=args.model,
                workspace_snapshot_ref=snapshot_ref,
                timeout_seconds=task.timeout_seconds,
                repo_root=repo_root,
            )
            result = runner.run_attempt(run_spec)
            results.append(result)
            if result.status == "incompatible":
                break

    cohort_root = repo_root / "runs" / "cohorts" / f"{args.task_id}__{args.provider}__{args.model.replace('/', '_')}"
    report_path = runner.write_cohort_report(results, cohort_root)
    (cohort_root / "results.json").write_text(
        json.dumps([item.to_dict() for item in results], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
