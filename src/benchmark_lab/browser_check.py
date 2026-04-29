from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

PLAYWRIGHT_STEP_TIMEOUT_SECONDS = 45


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
        try:
            return subprocess.run(
                [str(playwright_wrapper), *args],
                cwd=output_dir,
                env={**os.environ, **env},
                text=True,
                capture_output=True,
                check=False,
                timeout=PLAYWRIGHT_STEP_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                args=[str(playwright_wrapper), *args],
                returncode=124,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + f"\nTimed out after {PLAYWRIGHT_STEP_TIMEOUT_SECONDS}s",
            )

    def _run_js(expression: str) -> subprocess.CompletedProcess[str]:
        return _run("run-code", expression)

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

    snapshots: dict[str, str] = {}

    def _run_step(name: str, proc: subprocess.CompletedProcess[str]) -> bool:
        _record(name, proc)
        return bool(steps[-1]["passed"])

    def _extract_ref(snapshot_text: str, *patterns: str) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, snapshot_text)
            if match:
                return match.group(1)
        return None

    def _latest_snapshot_text() -> str:
        snapshot_dir = output_dir / ".playwright-cli"
        snapshots = sorted(snapshot_dir.glob("page-*.yml"), key=lambda path: path.stat().st_mtime)
        if not snapshots:
            return ""
        return snapshots[-1].read_text(encoding="utf-8")

    login_proc = _run("open", f"{admin_base}/login/")
    if _run_step("open_login", login_proc):
        login_snapshot = _latest_snapshot_text() or login_proc.stdout
        username_ref = _extract_ref(login_snapshot, r'textbox "Имя пользователя" \[ref=(e\d+)\]', r'textbox "Username" \[ref=(e\d+)\]')
        password_ref = _extract_ref(login_snapshot, r'textbox "Пароль" \[ref=(e\d+)\]', r'textbox "Password" \[ref=(e\d+)\]')
        submit_ref = _extract_ref(login_snapshot, r'button "Войти" \[ref=(e\d+)\]', r'button "Log in" \[ref=(e\d+)\]')
        if username_ref and password_ref and submit_ref:
            if _run_step("fill_username", _run("fill", username_ref, "admin")):
                if _run_step("fill_password", _run("fill", password_ref, "admin")):
                    if _run_step("submit_login", _run("click", submit_ref)):
                        list_nav = _run_js(f"page.goto('{admin_base}/files/media/')")
                        if _run_step("open_media_list", list_nav):
                            list_snapshot_proc = _run("snapshot")
                            snapshots["list"] = _latest_snapshot_text() or list_snapshot_proc.stdout
                            if _run_step("snapshot_list", list_snapshot_proc):
                                list_ok = "Content warning" in snapshots["list"] and "Playwright Content Warning Demo" in snapshots["list"]
                                steps.append(
                                    {
                                        "name": "assert_list_page",
                                        "passed": list_ok,
                                        "stdout": snapshots["list"].strip(),
                                        "stderr": "" if list_ok else "missing content warning column or seeded media row",
                                    }
                                )
                                if list_ok:
                                    change_nav = _run_js(f"page.goto('{admin_base}/files/media/{media_id}/change/')")
                                    if _run_step("open_media_change", change_nav):
                                        change_snapshot_proc = _run("snapshot")
                                        change_snapshot = _latest_snapshot_text() or change_snapshot_proc.stdout
                                        if _run_step("snapshot_change_form", change_snapshot_proc):
                                            select_ref = _extract_ref(
                                                change_snapshot,
                                                r'combobox "Content warning" \[ref=(e\d+)\]',
                                                r'select "Content warning" \[ref=(e\d+)\]',
                                                r'Content warning.*\[ref=(e\d+)\]',
                                            )
                                            save_ref = _extract_ref(
                                                change_snapshot,
                                                r'button "Save" \[ref=(e\d+)\]',
                                                r'button "Сохранить" \[ref=(e\d+)\]',
                                                r'button "Save and continue editing" \[ref=(e\d+)\]',
                                            )
                                            form_ok = select_ref is not None and save_ref is not None and expected_initial_value in change_snapshot
                                            steps.append(
                                                {
                                                    "name": "assert_change_form",
                                                    "passed": form_ok,
                                                    "stdout": change_snapshot.strip(),
                                                    "stderr": "" if form_ok else "missing content warning field, save button, or expected initial value",
                                                }
                                            )
                                            if form_ok and select_ref and save_ref:
                                                if _run_step("select_updated_value", _run("select", select_ref, updated_value)):
                                                    if _run_step("save_change", _run("click", save_ref)):
                                                        snapshot_proc = _run("snapshot")
                                                        snapshots["change"] = _latest_snapshot_text() or snapshot_proc.stdout
                                                        if _run_step("snapshot_change", snapshot_proc):
                                                            _run_step("close", _run("close"))
        else:
            steps.append(
                {
                    "name": "assert_login_form_refs",
                    "passed": False,
                    "stdout": login_snapshot.strip(),
                    "stderr": "missing username, password, or submit refs on login page",
                }
            )

    (output_dir / "admin-media-list.yml").write_text(snapshots.get("list", ""), encoding="utf-8")
    (output_dir / "admin-media-change.yml").write_text(snapshots.get("change", ""), encoding="utf-8")

    passed = all(step["passed"] for step in steps)
    browser_md = run_root / "browser-check.md"
    browser_md.write_text(
        "\n".join(
            [
                "# Playwright Browser Check",
                "",
                f"Run: `{run_root.name}`",
                "",
                f"- Admin list snapshot: [{(output_dir / 'admin-media-list.yml').name}]({output_dir / 'admin-media-list.yml'})",
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
            "admin_media_list_yml": str(output_dir / "admin-media-list.yml"),
            "admin_media_change_yml": str(output_dir / "admin-media-change.yml"),
        },
    }
