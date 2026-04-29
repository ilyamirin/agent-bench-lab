from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

PLAYWRIGHT_STEP_TIMEOUT_SECONDS = 45

ERROR_MARKERS = ("### Error", "SyntaxError:", "TypeError:", "Error:")
CONTENT_WARNING_LABELS = {
    "none": "None",
    "violence": "Violence",
    "strong-language": "Strong Language",
    "adult": "Adult Content",
    "disturbing-imagery": "Disturbing Imagery",
    "other": "Other",
}


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


def _command_passed(proc: subprocess.CompletedProcess[str]) -> bool:
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    return proc.returncode == 0 and not any(marker in stdout or marker in stderr for marker in ERROR_MARKERS)


def _latest_snapshot_path(output_dir: Path) -> Path | None:
    snapshot_dir = output_dir / ".playwright-cli"
    snapshots = sorted(snapshot_dir.glob("page-*.yml"), key=lambda path: path.name)
    return snapshots[-1] if snapshots else None


def _latest_snapshot_text(output_dir: Path) -> str:
    latest = _latest_snapshot_path(output_dir)
    if latest is None:
        return ""
    return latest.read_text(encoding="utf-8")


def _copy_latest_snapshot(output_dir: Path, target_name: str) -> Path | None:
    latest = _latest_snapshot_path(output_dir)
    if latest is None:
        return None
    target = output_dir / target_name
    target.write_text(latest.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _snapshot_text_from_stdout(stdout: str) -> str:
    match = re.search(r"### Snapshot\s+```yaml\n(.*?)\n```", stdout, re.DOTALL)
    return match.group(1) if match else ""


def _extract_ref(snapshot_text: str, *patterns: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, snapshot_text)
        if match:
            return match.group(1)
    return None


def _content_warning_selected(snapshot_text: str, expected_value: str) -> bool:
    label = CONTENT_WARNING_LABELS.get(expected_value, expected_value)
    return f'option "{label}" [selected]' in snapshot_text


def _content_warning_refs(snapshot_text: str) -> dict[str, str | None]:
    return {
        "content_warning_select": _extract_ref(
            snapshot_text,
            r'combobox "Content warning - Optional content warning for this media" \[ref=(e\d+)\]',
            r'combobox "Content warning" \[ref=(e\d+)\]',
            r'select "Content warning - Optional content warning for this media" \[ref=(e\d+)\]',
            r'select "Content warning" \[ref=(e\d+)\]',
        ),
        "submit_button": _extract_ref(
            snapshot_text,
            r'button "Update Media" \[ref=(e\d+)\]',
            r'button "Save" \[ref=(e\d+)\]',
            r'button "Сохранить" \[ref=(e\d+)\]',
        ),
    }


def _frontend_login_refs(snapshot_text: str) -> dict[str, str | None]:
    return {
        "username": _extract_ref(
            snapshot_text,
            r'textbox "Войти:" \[ref=(e\d+)\]',
            r'textbox "Имя пользователя или e-mail" \[ref=(e\d+)\]',
            r'textbox "Username or email" \[ref=(e\d+)\]',
        ),
        "password": _extract_ref(
            snapshot_text,
            r'textbox "Пароль:" \[ref=(e\d+)\]',
            r'textbox "Password:" \[ref=(e\d+)\]',
            r'textbox "Password" \[ref=(e\d+)\]',
        ),
        "submit": _extract_ref(
            snapshot_text,
            r'button "Sign In" \[ref=(e\d+)\]',
            r'button "Войти" \[ref=(e\d+)\]',
            r'button "Log in" \[ref=(e\d+)\]',
        ),
    }


def _view_page_refs(snapshot_text: str) -> dict[str, str | None]:
    return {
        "edit_link": _extract_ref(
            snapshot_text,
            r'link "edit" \[ref=(e\d+)\]',
            r'link "Edit" \[ref=(e\d+)\]',
        )
    }


def run_content_warning_browser_check(
    workspace_dir: Path,
    run_root: Path,
    media_id: int | None = None,
    media_slug: str = "playwright-content-warning",
    expected_initial_value: str = "adult",
    updated_value: str = "violence",
    web_port: int = 80,
) -> dict[str, object]:
    del workspace_dir
    del media_id
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

    steps: list[dict[str, object]] = []
    edit_url = f"http://127.0.0.1:{web_port}/edit?m={media_slug}"
    benchmark_username = "benchmark_user"
    benchmark_password = "benchmark-pass"

    def _record_proc_step(
        name: str,
        command: list[str],
        proc: subprocess.CompletedProcess[str],
        *,
        snapshot_path: Path | None = None,
        parsed_refs: dict[str, str | None] | None = None,
        required: bool = True,
    ) -> bool:
        steps.append(
            {
                "name": name,
                "command": command,
                "snapshot": str(snapshot_path) if snapshot_path is not None else None,
                "parsed_refs": parsed_refs or {},
                "required": required,
                "passed": _command_passed(proc),
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        )
        return bool(steps[-1]["passed"])

    def _record_assert_step(
        name: str,
        *,
        passed: bool,
        stdout: str = "",
        stderr: str = "",
        snapshot_path: Path | None = None,
        parsed_refs: dict[str, str | None] | None = None,
        required: bool = True,
    ) -> bool:
        steps.append(
            {
                "name": name,
                "command": ["assert"],
                "snapshot": str(snapshot_path) if snapshot_path is not None else None,
                "parsed_refs": parsed_refs or {},
                "required": required,
                "passed": passed,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
            }
        )
        return passed

    def _snapshot_step(name: str, target_name: str) -> tuple[bool, str, Path | None]:
        proc = _run("snapshot")
        snapshot_text = _snapshot_text_from_stdout(proc.stdout)
        snapshot_path: Path | None = None
        if snapshot_text:
            snapshot_path = output_dir / target_name
            snapshot_path.write_text(snapshot_text, encoding="utf-8")
        else:
            snapshot_path = _copy_latest_snapshot(output_dir, target_name)
            snapshot_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path is not None else ""
        passed = _record_proc_step(name, ["snapshot"], proc, snapshot_path=snapshot_path)
        return passed, snapshot_text, snapshot_path

    if not _record_proc_step("open_edit_entry", ["open", edit_url], _run("open", edit_url)):
        return _finalize_browser_check(run_root, steps, output_dir)
    if not _record_proc_step("resize_browser", ["resize", "1920", "1080"], _run("resize", "1920", "1080")):
        return _finalize_browser_check(run_root, steps, output_dir)

    entry_snapshot_ok, entry_snapshot, entry_snapshot_path = _snapshot_step("snapshot_entry", "entry-page.yml")
    if not entry_snapshot_ok:
        return _finalize_browser_check(run_root, steps, output_dir)

    edit_refs = _content_warning_refs(entry_snapshot)
    edit_snapshot = entry_snapshot
    edit_snapshot_path = entry_snapshot_path
    if not all(edit_refs.values()):
        login_refs = _frontend_login_refs(entry_snapshot)
        if not _record_assert_step(
            "assert_frontend_login_refs",
            passed=all(login_refs.values()),
            stdout=entry_snapshot,
            stderr="" if all(login_refs.values()) else "missing username, password, or submit ref on frontend sign-in page",
            snapshot_path=entry_snapshot_path,
            parsed_refs=login_refs,
        ):
            return _finalize_browser_check(run_root, steps, output_dir)

        if not _record_proc_step(
            "fill_frontend_username",
            ["fill", login_refs["username"], benchmark_username],
            _run("fill", str(login_refs["username"]), benchmark_username),
        ):
            return _finalize_browser_check(run_root, steps, output_dir)
        if not _record_proc_step(
            "fill_frontend_password",
            ["fill", login_refs["password"], benchmark_password],
            _run("fill", str(login_refs["password"]), benchmark_password),
        ):
            return _finalize_browser_check(run_root, steps, output_dir)
        if not _record_proc_step(
            "submit_frontend_login",
            ["click", login_refs["submit"]],
            _run("click", str(login_refs["submit"])),
        ):
            return _finalize_browser_check(run_root, steps, output_dir)

        edit_snapshot_ok, edit_snapshot, edit_snapshot_path = _snapshot_step("snapshot_post_login", "post-login.yml")
        if not edit_snapshot_ok:
            return _finalize_browser_check(run_root, steps, output_dir)
        edit_refs = _content_warning_refs(edit_snapshot)
        if edit_snapshot_path is not None:
            user_edit_target = output_dir / "user-edit-form.yml"
            user_edit_target.write_text(edit_snapshot_path.read_text(encoding="utf-8"), encoding="utf-8")
            edit_snapshot_path = user_edit_target
    else:
        entry_target = output_dir / "entry-page.yml"
        user_edit_target = output_dir / "user-edit-form.yml"
        if entry_target.exists():
            user_edit_target.write_text(entry_target.read_text(encoding="utf-8"), encoding="utf-8")
            edit_snapshot_path = user_edit_target

    if not _record_assert_step(
        "assert_edit_form_refs",
        passed=all(edit_refs.values()),
        stdout=edit_snapshot,
        stderr="" if all(edit_refs.values()) else "missing content_warning select or submit button on edit page",
        snapshot_path=edit_snapshot_path,
        parsed_refs=edit_refs,
    ):
        return _finalize_browser_check(run_root, steps, output_dir)

    if not _record_assert_step(
        "assert_initial_value",
        passed=_content_warning_selected(edit_snapshot, expected_initial_value),
        stdout=edit_snapshot,
        stderr="" if _content_warning_selected(edit_snapshot, expected_initial_value) else f"expected initial content_warning={expected_initial_value}",
        snapshot_path=edit_snapshot_path,
        parsed_refs=edit_refs,
    ):
        return _finalize_browser_check(run_root, steps, output_dir)

    if not _record_proc_step(
        "select_updated_value",
        ["select", edit_refs["content_warning_select"], updated_value],
        _run("select", str(edit_refs["content_warning_select"]), updated_value),
        snapshot_path=edit_snapshot_path,
        parsed_refs=edit_refs,
    ):
        return _finalize_browser_check(run_root, steps, output_dir)
    if not _record_proc_step(
        "submit_edit_form",
        ["click", edit_refs["submit_button"]],
        _run("click", str(edit_refs["submit_button"])),
        snapshot_path=edit_snapshot_path,
        parsed_refs=edit_refs,
    ):
        return _finalize_browser_check(run_root, steps, output_dir)

    post_submit_ok, post_submit_snapshot, post_submit_path = _snapshot_step("snapshot_after_submit", "post-submit.yml")
    if not post_submit_ok:
        return _finalize_browser_check(run_root, steps, output_dir)
    view_refs = _view_page_refs(post_submit_snapshot)
    if not _record_assert_step(
        "assert_view_page_edit_link",
        passed=bool(view_refs["edit_link"]),
        stdout=post_submit_snapshot,
        stderr="" if view_refs["edit_link"] else "missing edit link on post-submit view page",
        snapshot_path=post_submit_path,
        parsed_refs=view_refs,
    ):
        return _finalize_browser_check(run_root, steps, output_dir)
    reopen_clicked = _record_proc_step(
        "reopen_edit_page",
        ["click", view_refs["edit_link"]],
        _run("click", str(view_refs["edit_link"])),
        required=False,
    )
    if not reopen_clicked:
        reopen_clicked = _record_proc_step(
            "reopen_edit_page_eval",
            ["eval", "el => el.click()", view_refs["edit_link"]],
            _run("eval", "el => el.click()", str(view_refs["edit_link"])),
            required=False,
        )
    if not reopen_clicked:
        reopen_clicked = _record_proc_step(
            "reopen_edit_page_eval_href",
            ["eval", "el => (window.location.href = el.href)", view_refs["edit_link"]],
            _run("eval", "el => (window.location.href = el.href)", str(view_refs["edit_link"])),
            required=False,
        )
    if not _record_assert_step(
        "assert_reopen_navigation",
        passed=reopen_clicked,
        stderr="" if reopen_clicked else "all reopen edit page strategies failed",
    ):
        return _finalize_browser_check(run_root, steps, output_dir)
    if not reopen_clicked:
        return _finalize_browser_check(run_root, steps, output_dir)

    reopen_ok, reopen_snapshot, reopen_snapshot_path = _snapshot_step("snapshot_reopened_edit_page", "user-edit-form-updated.yml")
    if not reopen_ok:
        return _finalize_browser_check(run_root, steps, output_dir)

    reopen_refs = _content_warning_refs(reopen_snapshot)
    _record_assert_step(
        "assert_reopened_persisted_value",
        passed=_content_warning_selected(reopen_snapshot, updated_value),
        stdout=reopen_snapshot,
        stderr="" if _content_warning_selected(reopen_snapshot, updated_value) else f"expected reopened content_warning={updated_value}",
        snapshot_path=reopen_snapshot_path,
        parsed_refs=reopen_refs,
    )

    _record_proc_step("close", ["close"], _run("close"))
    return _finalize_browser_check(run_root, steps, output_dir)


def _finalize_browser_check(run_root: Path, steps: list[dict[str, object]], output_dir: Path) -> dict[str, object]:
    browser_md = run_root / "browser-check.md"
    passed = bool(steps) and all(
        bool(step["passed"])
        for step in steps
        if bool(step.get("required", True))
    )
    user_edit_form = output_dir / "user-edit-form.yml"
    user_edit_form_updated = output_dir / "user-edit-form-updated.yml"
    browser_md.write_text(
        "\n".join(
            [
                "# Playwright Browser Check",
                "",
                f"Run: `{run_root.name}`",
                "",
                f"- User edit snapshot: [{user_edit_form.name}](playwright/{user_edit_form.name})" if user_edit_form.exists() else "- User edit snapshot: not captured",
                f"- Reopened edit snapshot: [{user_edit_form_updated.name}](playwright/{user_edit_form_updated.name})" if user_edit_form_updated.exists() else "- Reopened edit snapshot: not captured",
                "",
                "## Steps",
                *[
                    f"- `{step['name']}`: {'passed' if step['passed'] else 'failed'}"
                    + ("" if step.get("required", True) else " (non-blocking)")
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
            "user_edit_form_yml": str(user_edit_form),
            "user_edit_form_updated_yml": str(user_edit_form_updated),
        },
    }


def run_admin_browser_check(
    workspace_dir: Path,
    run_root: Path,
    media_id: int,
    expected_initial_value: str = "adult",
    updated_value: str = "violence",
    web_port: int = 80,
) -> dict[str, object]:
    return run_content_warning_browser_check(
        workspace_dir=workspace_dir,
        run_root=run_root,
        media_id=media_id,
        expected_initial_value=expected_initial_value,
        updated_value=updated_value,
        web_port=web_port,
    )
