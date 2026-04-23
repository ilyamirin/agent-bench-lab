from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path


def _resolve_playwright_wrapper() -> Path:
    override = os.environ.get("PLAYWRIGHT_CLI_WRAPPER")
    if override:
        wrapper = Path(override)
        if wrapper.exists():
            return wrapper
        raise FileNotFoundError(
            f"Playwright wrapper from PLAYWRIGHT_CLI_WRAPPER was not found: {wrapper}"
        )

    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        wrapper = Path(codex_home) / "skills" / "playwright" / "scripts" / "playwright_cli.sh"
        if wrapper.exists():
            return wrapper
        raise FileNotFoundError(
            f"Playwright wrapper derived from CODEX_HOME was not found: {wrapper}"
        )

    wrapper = Path.home() / ".codex" / "skills" / "playwright" / "scripts" / "playwright_cli.sh"
    if wrapper.exists():
        return wrapper
    raise FileNotFoundError(
        "Playwright wrapper was not found. Set PLAYWRIGHT_CLI_WRAPPER or CODEX_HOME, "
        f"or install the wrapper at the default path: {wrapper}"
    )


def run_admin_browser_check(
    workspace_dir: Path,
    run_root: Path,
    media_id: int,
    expected_initial_value: str = "adult",
    updated_value: str = "violence",
    web_port: int = 80,
) -> dict[str, object]:
    playwright_wrapper = _resolve_playwright_wrapper()
    output_dir = run_root / "playwright"
    output_dir.mkdir(parents=True, exist_ok=True)
    session = "pw-" + hashlib.sha1(run_root.name.encode("utf-8")).hexdigest()[:12]
    env = {"PLAYWRIGHT_CLI_SESSION": session}

    def _run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(playwright_wrapper), *args],
            cwd=output_dir,
            env={**os.environ, **env},
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_code(script: str) -> subprocess.CompletedProcess[str]:
        wrapped = f"(async () => {{ {script} }})().catch(err => {{ console.error(err); process.exit(1); }});"
        return _run("run-code", wrapped)

    steps: list[dict[str, object]] = []
    admin_base = f"http://127.0.0.1:{web_port}/admin"

    def _record(name: str, proc: subprocess.CompletedProcess[str]) -> None:
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        error_markers = ("### Error", "SyntaxError:", "Error:")
        steps.append(
            {
                "name": name,
                "passed": proc.returncode == 0
                and not any(marker in stdout for marker in error_markers)
                and not any(marker in stderr for marker in error_markers),
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    commands = [
        ("open_login", _run("open", f"{admin_base}/login/")),
        (
            "login",
            _run_code(
                (
                    # These are seeded benchmark-only admin credentials for local verification.
                    "await page.locator('input[name=\"username\"]').fill('admin');"
                    "await page.locator('input[name=\"password\"]').fill('admin');"
                    "await page.locator('input[type=\"submit\"]').click();"
                    "await page.waitForLoadState('networkidle');"
                ),
            ),
        ),
        ("open_media_list", _run("open", f"{admin_base}/files/media/")),
        (
            "assert_list_page",
            _run_code(
                (
                    "const body = await page.locator('body').innerText();"
                    "if (!body.includes('Content warning')) throw new Error('missing content warning column');"
                    "if (!body.includes('Playwright Content Warning Demo')) throw new Error('missing seeded media row');"
                ),
            ),
        ),
        (
            "screenshot_list",
            _run_code(
                f"await page.screenshot({{path: {str(output_dir / 'admin-media-list.png')!r}, fullPage: true}})",
            ),
        ),
        ("snapshot_list", _run("snapshot")),
        ("open_media_change", _run("open", f"{admin_base}/files/media/{media_id}/change/")),
        (
            "assert_change_form",
            _run_code(
                (
                    f"const initial = await page.locator('select[name=\"content_warning\"]').inputValue();"
                    f"if (initial !== '{expected_initial_value}') throw new Error(`unexpected initial value ${'{'}initial{'}'}`);"
                ),
            ),
        ),
        (
            "update_value",
            _run_code(
                (
                    f"await page.selectOption('select[name=\"content_warning\"]', '{updated_value}');"
                    "await page.locator('input[name=\"_save\"]').click();"
                    "await page.waitForLoadState('networkidle');"
                ),
            ),
        ),
        (
            "screenshot_change",
            _run_code(
                f"await page.screenshot({{path: {str(output_dir / 'admin-media-change.png')!r}, fullPage: true}})",
            ),
        ),
        ("snapshot_change", _run("snapshot")),
        ("close", _run("close")),
    ]
    for name, proc in commands:
        _record(name, proc)

    (output_dir / "admin-media-list.yml").write_text(commands[5][1].stdout, encoding="utf-8")
    (output_dir / "admin-media-change.yml").write_text(commands[9][1].stdout, encoding="utf-8")

    passed = all(step["passed"] for step in steps)
    browser_md = run_root / "browser-check.md"
    browser_md.write_text(
        "\n".join(
            [
                "# Playwright Browser Check",
                "",
                f"Run: `{run_root.name}`",
                "",
                f"- Admin list screenshot: [{(output_dir / 'admin-media-list.png').name}]({output_dir / 'admin-media-list.png'})",
                f"- Admin list snapshot: [{(output_dir / 'admin-media-list.yml').name}]({output_dir / 'admin-media-list.yml'})",
                f"- Admin change screenshot: [{(output_dir / 'admin-media-change.png').name}]({output_dir / 'admin-media-change.png'})",
                f"- Admin change snapshot: [{(output_dir / 'admin-media-change.yml').name}]({output_dir / 'admin-media-change.yml'})",
                "",
                "## Steps",
                *[
                    f"- `{step['name']}`: {'passed' if step['passed'] else 'failed'}"
                    for step in steps
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "passed": passed,
        "steps": steps,
        "artifacts": {
            "browser_check_md": str(browser_md),
            "admin_media_list_png": str(output_dir / "admin-media-list.png"),
            "admin_media_list_yml": str(output_dir / "admin-media-list.yml"),
            "admin_media_change_png": str(output_dir / "admin-media-change.png"),
            "admin_media_change_yml": str(output_dir / "admin-media-change.yml"),
        },
    }
