from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmark_lab.browser_check import (
    _content_warning_refs,
    _latest_snapshot_path,
    _snapshot_text_from_stdout,
    run_content_warning_browser_check,
)


LOGIN_SNAPSHOT = """
- textbox "Войти:" [ref=e11]
- textbox "Пароль:" [ref=e12]
- button "Sign In" [ref=e13]
""".strip()

EDIT_SNAPSHOT_ADULT = """
- combobox "Content warning - Optional content warning for this media" [ref=e181]:
  - option "None"
  - option "Violence"
  - option "Adult Content" [selected]
- button "Update Media" [ref=e184]
""".strip()

EDIT_SNAPSHOT_VIOLENCE = """
- combobox "Content warning - Optional content warning for this media" [ref=e181]:
  - option "None"
  - option "Violence" [selected]
  - option "Adult Content"
- button "Update Media" [ref=e184]
""".strip()

VIEW_SNAPSHOT = """
- link "edit" [ref=e256]
""".strip()


class BrowserCheckHelpersTest(unittest.TestCase):
    def test_content_warning_refs_are_parsed_from_snapshot(self) -> None:
        refs = _content_warning_refs(EDIT_SNAPSHOT_ADULT)
        self.assertEqual(refs["content_warning_select"], "e181")
        self.assertEqual(refs["submit_button"], "e184")

    def test_latest_snapshot_uses_timestamped_filename_order(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="browser-check-snapshots-"))
        snapshot_dir = temp_dir / ".playwright-cli"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        older = snapshot_dir / "page-2026-04-29T19-09-26-646Z.yml"
        newer = snapshot_dir / "page-2026-04-29T19-09-33-715Z.yml"
        older.write_text("older", encoding="utf-8")
        newer.write_text("newer", encoding="utf-8")
        self.assertEqual(_latest_snapshot_path(temp_dir), newer)

    def test_snapshot_text_is_extracted_from_stdout_yaml_block(self) -> None:
        stdout = "### Page\n- Page URL: http://example.test\n### Snapshot\n```yaml\n- button \"Save\" [ref=e1]\n```\n"
        self.assertEqual(_snapshot_text_from_stdout(stdout), '- button "Save" [ref=e1]')


class BrowserCheckFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="browser-check-"))
        self.workspace_dir = self.temp_dir / "workspace"
        self.run_root = self.temp_dir / "run"
        self.run_root.mkdir(parents=True, exist_ok=True)

    def _write_snapshot(self, output_dir: Path, counter: int, text: str) -> None:
        snapshot_dir = output_dir / ".playwright-cli"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"page-{counter:02d}.yml"
        snapshot_path.write_text(text, encoding="utf-8")

    def _proc(self, cmd: list[str], *, returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=cmd, returncode=returncode, stdout=stdout, stderr=stderr)

    def test_missing_login_refs_are_reported_explicitly(self) -> None:
        snapshots = iter(
            [
                """
- textbox "Имя пользователя" [ref=e11]
- textbox "Пароль" [ref=e12]
""".strip(),
            ]
        )

        def fake_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
            if cmd[1] == "snapshot":
                self._write_snapshot(Path(kwargs["cwd"]), 1, next(snapshots))
            return self._proc(cmd)

        with (
            patch("benchmark_lab.browser_check._resolve_playwright_wrapper", return_value=Path("/tmp/playwright_cli.sh")),
            patch("benchmark_lab.browser_check.subprocess.run", side_effect=fake_run),
        ):
            result = run_content_warning_browser_check(self.workspace_dir, self.run_root, media_id=123, web_port=8123)

        self.assertFalse(result["passed"])
        failed = [step for step in result["steps"] if not step["passed"]]
        self.assertEqual(failed[-1]["name"], "assert_frontend_login_refs")

    def test_incomplete_flow_cannot_report_success(self) -> None:
        snapshots = iter([LOGIN_SNAPSHOT, EDIT_SNAPSHOT_ADULT])

        def fake_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
            if cmd[1] == "snapshot":
                self._write_snapshot(Path(kwargs["cwd"]), len(list((Path(kwargs["cwd"]) / ".playwright-cli").glob("page-*.yml"))) + 1, next(snapshots))
                return self._proc(cmd)
            if cmd[1] == "select":
                return self._proc(cmd, returncode=1, stderr="select failed")
            return self._proc(cmd)

        with (
            patch("benchmark_lab.browser_check._resolve_playwright_wrapper", return_value=Path("/tmp/playwright_cli.sh")),
            patch("benchmark_lab.browser_check.subprocess.run", side_effect=fake_run),
        ):
            result = run_content_warning_browser_check(self.workspace_dir, self.run_root, media_id=123, web_port=8123)

        self.assertFalse(result["passed"])
        self.assertIn("select_updated_value", [step["name"] for step in result["steps"]])

    def test_user_flow_passes_without_run_code(self) -> None:
        snapshots = iter(
            [
                LOGIN_SNAPSHOT,
                EDIT_SNAPSHOT_ADULT,
                VIEW_SNAPSHOT,
                EDIT_SNAPSHOT_VIOLENCE,
            ]
        )
        commands: list[list[str]] = []
        counter = {"value": 0}

        def fake_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
            commands.append(cmd[1:])
            if cmd[1] == "snapshot":
                counter["value"] += 1
                self._write_snapshot(Path(kwargs["cwd"]), counter["value"], next(snapshots))
            return self._proc(cmd)

        with (
            patch("benchmark_lab.browser_check._resolve_playwright_wrapper", return_value=Path("/tmp/playwright_cli.sh")),
            patch("benchmark_lab.browser_check.subprocess.run", side_effect=fake_run),
        ):
            result = run_content_warning_browser_check(self.workspace_dir, self.run_root, media_id=123, web_port=8123)

        self.assertTrue(result["passed"])
        self.assertTrue(any(step["name"] == "assert_reopened_persisted_value" and step["passed"] for step in result["steps"]))
        self.assertFalse(any(command and command[0] == "run-code" for command in commands))

    def test_failed_reopen_click_does_not_poison_successful_fallback(self) -> None:
        snapshots = iter(
            [
                LOGIN_SNAPSHOT,
                EDIT_SNAPSHOT_ADULT,
                VIEW_SNAPSHOT,
                EDIT_SNAPSHOT_VIOLENCE,
            ]
        )
        counter = {"value": 0}

        def fake_run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
            if cmd[1] == "snapshot":
                counter["value"] += 1
                self._write_snapshot(Path(kwargs["cwd"]), counter["value"], next(snapshots))
                return self._proc(cmd)
            if cmd[1] == "click" and len(cmd) > 2 and cmd[2] == "e256":
                return self._proc(cmd, returncode=1, stdout="### Error\nTimeoutError: click intercepted")
            return self._proc(cmd)

        with (
            patch("benchmark_lab.browser_check._resolve_playwright_wrapper", return_value=Path("/tmp/playwright_cli.sh")),
            patch("benchmark_lab.browser_check.subprocess.run", side_effect=fake_run),
        ):
            result = run_content_warning_browser_check(self.workspace_dir, self.run_root, media_id=123, web_port=8123)

        self.assertTrue(result["passed"])
        self.assertTrue(any(step["name"] == "reopen_edit_page" and not step["passed"] for step in result["steps"]))
        self.assertTrue(any(step["name"] == "reopen_edit_page_eval" and step["passed"] for step in result["steps"]))
        self.assertTrue(any(step["name"] == "assert_reopen_navigation" and step["passed"] for step in result["steps"]))


if __name__ == "__main__":
    unittest.main()
