from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenRouter key", re.compile(r"sk-or-v1-[A-Za-z0-9]{32,}")),
    ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("GitHub personal access token", re.compile(r"\bghp_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Explicit API key assignment", re.compile(r"(OPENROUTER|OPENAI|ANTHROPIC|GEMINI|GOOGLE)_API_KEY\s*[:=]\s*[\"'][^\"']+[\"']")),
]


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    )


def staged_paths() -> list[str]:
    output = run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR").stdout
    return [line for line in output.splitlines() if line.strip()]


def is_submodule(path: str) -> bool:
    result = run_git("ls-files", "--stage", "--", path).stdout.strip()
    if not result:
        return False
    return result.split()[0] == "160000"


def staged_text(path: str) -> str | None:
    try:
        data = subprocess.run(
            ["git", "show", f":{path}"],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None

    if b"\x00" in data:
        return None

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    repo_root = Path(run_git("rev-parse", "--show-toplevel").stdout.strip())
    matches: list[tuple[str, str, int, str]] = []

    for path in staged_paths():
        if is_submodule(path):
            continue

        text = staged_text(path)
        if text is None:
            continue

        for label, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line_number = text.count("\n", 0, match.start()) + 1
                line = text.splitlines()[line_number - 1].strip() if text.splitlines() else ""
                matches.append((path, label, line_number, line[:160]))

    if not matches:
        print("secret scan: OK")
        return 0

    print("secret scan: blocked potential secret(s) in staged content", file=sys.stderr)
    for path, label, line_number, preview in matches:
        print(
            f"  - {path}:{line_number}: {label}: {preview}",
            file=sys.stderr,
        )
    print(
        f"review staged files in {repo_root} and remove or redact secrets before committing",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
