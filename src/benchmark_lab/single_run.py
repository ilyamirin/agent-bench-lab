from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import RunSpec
from .runner import BenchmarkRunner


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one benchmark attempt for one agent")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--task-id", default="simple_content_warning")
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--model", default="qwen/qwen3.6-plus")
    parser.add_argument("--agent", required=True, help="Agent adapter id")
    parser.add_argument("--attempt", type=int, required=True, help="Attempt number")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    runner = BenchmarkRunner(repo_root)
    task = runner.load_task(args.task_id)
    run_spec = RunSpec(
        agent_id=args.agent,
        task_id=args.task_id,
        attempt=args.attempt,
        provider=args.provider,
        model=args.model,
        workspace_snapshot_ref=runner.workspace_snapshot_ref(),
        timeout_seconds=task.timeout_seconds,
        repo_root=repo_root,
    )
    result = runner.run_attempt(run_spec)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
