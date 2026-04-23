#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LICENSE_FILE = REPO_ROOT / "LICENSE"
THIRD_PARTY_FILE = REPO_ROOT / "THIRD_PARTY.md"
GITMODULES_FILE = REPO_ROOT / ".gitmodules"
SUBMODULE_PATH = REPO_ROOT / "upstream" / "mediacms"

MARKDOWN_LINK_LOCAL = re.compile(r"\]\((?:\.\./|\./)?(?:\.agents/|runs/)[^)]+\)")
MACHINE_LOCAL_PATH = re.compile(r"(/Users/[^/\s)]+|[A-Za-z]:\\Users\\[^\\\s)]+)")


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _tracked_files() -> list[Path]:
    proc = _run("git", "ls-files")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git ls-files failed")
    return [REPO_ROOT / line for line in proc.stdout.splitlines() if line.strip()]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    issues: list[str] = []

    if not LICENSE_FILE.exists():
        issues.append("Missing root LICENSE file.")
    if not THIRD_PARTY_FILE.exists():
        issues.append("Missing root THIRD_PARTY.md file.")

    gitmodules_text = _read_text(GITMODULES_FILE) if GITMODULES_FILE.exists() else ""
    third_party_text = _read_text(THIRD_PARTY_FILE) if THIRD_PARTY_FILE.exists() else ""
    mediacms_url = "https://github.com/mediacms-io/mediacms.git"
    if mediacms_url not in gitmodules_text:
        issues.append(".gitmodules does not contain the expected MediaCMS URL.")
    if mediacms_url not in third_party_text:
        issues.append("THIRD_PARTY.md does not mention the MediaCMS submodule URL from .gitmodules.")

    try:
        tracked_files = _tracked_files()
    except RuntimeError as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 2

    for path in tracked_files:
        if path.is_dir():
            continue
        text = _read_text(path)
        rel = path.relative_to(REPO_ROOT)
        if MARKDOWN_LINK_LOCAL.search(text):
            issues.append(f"{rel}: contains markdown links into local-only .agents/ or runs/ paths.")
        if MACHINE_LOCAL_PATH.search(text):
            issues.append(f"{rel}: contains machine-local absolute paths.")

    submodule_status = _run(
        "git",
        "-C",
        str(SUBMODULE_PATH),
        "status",
        "--short",
        "--untracked-files=all",
    )
    if submodule_status.returncode != 0:
        issues.append(
            "Unable to read upstream/mediacms git status: "
            + (submodule_status.stderr.strip() or "unknown error")
        )
    elif submodule_status.stdout.strip():
        issues.append("upstream/mediacms is not clean.")

    if issues:
        print("Public repo audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Public repo audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
