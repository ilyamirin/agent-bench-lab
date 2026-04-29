from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from .browser_check import _resolve_playwright_wrapper, run_admin_browser_check


def _run_playwright(output_dir: Path, session: str, *args: str) -> subprocess.CompletedProcess[str]:
    wrapper = _resolve_playwright_wrapper()
    return subprocess.run(
        [str(wrapper), *args],
        cwd=output_dir,
        env={**os.environ, "PLAYWRIGHT_CLI_SESSION": session},
        text=True,
        capture_output=True,
        check=False,
    )


def _run_code(output_dir: Path, session: str, script: str) -> subprocess.CompletedProcess[str]:
    wrapped = f"(async () => {{ {script} }})().catch(err => {{ console.error(err); process.exit(1); }});"
    return _run_playwright(output_dir, session, "run-code", wrapped)


def run_frontend_content_warning_surface(
    workspace_dir: Path,
    run_root: Path,
    web_port: int,
    media_slug: str = "playwright-content-warning",
) -> dict[str, object]:
    output_dir = run_root / "playwright"
    output_dir.mkdir(parents=True, exist_ok=True)
    session = f"pw-frontend-{run_root.name}"
    url = f"http://127.0.0.1:{web_port}/edit?m={media_slug}"
    steps: list[dict[str, object]] = []

    def _record(name: str, proc: subprocess.CompletedProcess[str]) -> None:
        steps.append(
            {
                "name": name,
                "passed": proc.returncode == 0 and "Error:" not in proc.stdout and "Error:" not in proc.stderr,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        )

    _record("open_edit_page", _run_playwright(output_dir, session, "open", url))
    _record(
        "assert_select_exists",
        _run_code(
            output_dir,
            session,
            "await page.locator('select[name=\"content_warning\"]').waitFor({ state: 'visible', timeout: 15000 });",
        ),
    )
    _record(
        "screenshot_edit_page",
        _run_code(
            output_dir,
            session,
            f"await page.screenshot({{path: {str(output_dir / 'frontend-edit-form.png')!r}, fullPage: true}});",
        ),
    )
    snapshot = _run_playwright(output_dir, session, "snapshot")
    _record("snapshot_edit_page", snapshot)
    _record("close", _run_playwright(output_dir, session, "close"))

    (output_dir / "frontend-edit-form.yml").write_text(snapshot.stdout, encoding="utf-8")
    return {
        "passed": all(step["passed"] for step in steps),
        "steps": steps,
        "artifacts": {
            "frontend_edit_form_png": str(output_dir / "frontend-edit-form.png"),
            "frontend_edit_form_yml": str(output_dir / "frontend-edit-form.yml"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--web-port", required=True, type=int)
    parser.add_argument("--media-id", type=int)
    parser.add_argument("--media-slug", default="playwright-content-warning")
    args = parser.parse_args()

    workspace_dir = Path(args.workspace)
    run_root = Path(args.run_root)

    if args.scenario == "admin_content_warning_surface":
        if args.media_id is None:
            raise SystemExit("--media-id is required for admin_content_warning_surface")
        result = run_admin_browser_check(workspace_dir, run_root, args.media_id, web_port=args.web_port)
    elif args.scenario == "frontend_content_warning_surface":
        result = run_frontend_content_warning_surface(
            workspace_dir=workspace_dir,
            run_root=run_root,
            web_port=args.web_port,
            media_slug=args.media_slug,
        )
    else:
        raise SystemExit(f"Unknown scenario: {args.scenario}")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
