from __future__ import annotations

import argparse
import json
from pathlib import Path

from .browser_check import run_content_warning_browser_check


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

    if args.scenario not in {"admin_content_warning_surface", "frontend_content_warning_surface"}:
        raise SystemExit(f"Unknown scenario: {args.scenario}")

    result = run_content_warning_browser_check(
        workspace_dir=workspace_dir,
        run_root=run_root,
        media_id=args.media_id,
        media_slug=args.media_slug,
        web_port=args.web_port,
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
