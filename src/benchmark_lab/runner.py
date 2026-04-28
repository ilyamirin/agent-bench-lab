from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from shlex import quote

from .adapters import build_adapter_registry
from .browser_check import run_admin_browser_check
from .models import (
    CompatibilityResult,
    CompatibilityStatus,
    RunResult,
    RunSpec,
    RunStatus,
    ScoreCard,
)
from .reporting import (
    render_cohort_summary,
    render_markdown_summary,
    render_radar_chart_svg,
    write_preflight_json,
    write_run_result_json,
)
from .scoring import score_v1
from .tasks import TaskManifest, load_task_manifest
from .workspace import create_workspace_snapshot


class BenchmarkRunner:
    BROWSER_COMPOSE_TIMEOUT_SECONDS = 60

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.adapters = build_adapter_registry()

    def adapter_for(self, agent_id: str):
        try:
            return self.adapters[agent_id]
        except KeyError as exc:
            raise KeyError(f"Unknown agent adapter: {agent_id}") from exc

    def load_task(self, task_id: str) -> TaskManifest:
        path = self.repo_root / "benchmark" / "tasks" / f"{task_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Task manifest not found: {path}")
        return load_task_manifest(path)

    def workspace_snapshot_ref(self) -> str:
        proc = subprocess.run(
            ["git", "-C", str(self.repo_root / "upstream" / "mediacms"), "rev-parse", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        )
        return f"mediacms@{proc.stdout.strip()}"

    def prepare_workspace(self, run_spec: RunSpec, git_root: Path | None = None) -> Path:
        workspace_dir = create_workspace_snapshot(self.repo_root, run_spec.run_root / "workspace")
        self._configure_workspace_ports(run_spec, workspace_dir)
        repo_dir = git_root or workspace_dir
        subprocess.run(["git", "init"], cwd=repo_dir, text=True, capture_output=True, check=True)
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, text=True, capture_output=True, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Benchmark Runner",
                "-c",
                "user.email=benchmark@example.com",
                "commit",
                "-m",
                "benchmark baseline",
            ],
            cwd=repo_dir,
            text=True,
            capture_output=True,
            check=True,
        )
        return workspace_dir

    def _configure_workspace_ports(self, run_spec: RunSpec, workspace_dir: Path) -> None:
        compose_path = workspace_dir / "upstream" / "mediacms" / "docker-compose-dev.yaml"
        content = compose_path.read_text(encoding="utf-8")
        updated = content.replace('- "80:80"', f'- "127.0.0.1:{run_spec.web_port}:80"')
        compose_path.write_text(updated, encoding="utf-8")

    def _agent_home(self, run_spec: RunSpec) -> Path:
        return run_spec.run_root / "home"

    def _result_paths(self, run_spec: RunSpec) -> dict[str, Path]:
        run_root = run_spec.run_root
        return {
            "stdout": run_root / "stdout.log",
            "stderr": run_root / "stderr.log",
            "patch": run_root / "changes.patch",
            "result": run_root / "result.json",
            "summary": run_root / "summary.md",
            "radar": run_root / "radar.svg",
            "preflight": run_root / "preflight.json",
        }

    def _render_run_artifacts(self, run_result: RunResult) -> None:
        paths = self._result_paths(run_result.run_spec)
        write_run_result_json(run_result, paths["result"])
        paths["summary"].write_text(render_markdown_summary([run_result]), encoding="utf-8")
        paths["radar"].write_text(
            render_radar_chart_svg(run_result.run_spec.agent_id, run_result.scores),
            encoding="utf-8",
        )

    def _build_incompatible_result(
        self,
        run_spec: RunSpec,
        compatibility: CompatibilityResult,
    ) -> RunResult:
        return RunResult(
            run_spec=run_spec,
            compatibility=compatibility,
            status=RunStatus.INCOMPATIBLE,
            exit_code=None,
            duration_seconds=None,
            stdout_path=None,
            stderr_path=None,
            patch_path=None,
            scores=ScoreCard(
                task_solved=0,
                reliability=None,
                quality=None,
                speed_cost=None,
                pending_axes=["reliability", "quality", "speed/cost"],
            ),
            automated_checks=[],
            manual_review={"status": "pending"},
            actual_provider=run_spec.provider,
            actual_model=run_spec.model,
        )

    def _build_infra_error_result(
        self,
        run_spec: RunSpec,
        compatibility: CompatibilityResult,
        *,
        check_name: str,
        artifact_path: Path,
        command: list[str],
        returncode: int | None,
        stdout: str,
        stderr: str,
        duration_seconds: float | None = 0.0,
    ) -> RunResult:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(
                {
                    "command": command,
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return RunResult(
            run_spec=run_spec,
            compatibility=compatibility,
            status=RunStatus.INFRA_ERROR,
            exit_code=returncode,
            duration_seconds=duration_seconds,
            stdout_path=artifact_path,
            stderr_path=None,
            patch_path=None,
            scores=ScoreCard(
                task_solved=0,
                reliability=None,
                quality=None,
                speed_cost=None,
                pending_axes=["reliability", "quality", "speed/cost"],
            ),
            automated_checks=[
                {
                    "name": check_name,
                    "passed": False,
                    "artifact": str(artifact_path),
                    "returncode": returncode,
                }
            ],
            manual_review={"status": "pending"},
            actual_provider=run_spec.provider,
            actual_model=run_spec.model,
            run_metadata={},
        )

    def build_prompt(self, task: TaskManifest) -> str:
        constraints = task.extra.get("task_prompt_constraints", [])
        constraint_block = "\n".join(f"- {item}" for item in constraints)
        return (
            "You are participating in a coding-agent benchmark.\n\n"
            f"Task: {task.title}\n"
            f"Difficulty: {task.difficulty}\n\n"
            f"Instructions:\n{task.instructions}\n\n"
            "Repository layout:\n"
            "- if the current working directory already contains manage.py, files/, and frontend/, you are at the MediaCMS app root\n"
            "- otherwise, the target app to modify is upstream/mediacms\n"
            "- do not modify benchmark harness files\n\n"
            f"Constraints:\n{constraint_block}\n\n"
            "When finished, leave the code edits in place and summarize what you changed."
        ).strip()

    def _resolve_openrouter_api_key(self) -> str:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key:
            return api_key
        settings_path = self.repo_root / ".qwen" / "settings.json"
        if settings_path.exists():
            try:
                payload = json.loads(settings_path.read_text(encoding="utf-8"))
                api_key = payload.get("env", {}).get("OPENROUTER_API_KEY") or payload["security"]["auth"]["apiKey"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise RuntimeError(f"Unable to read OpenRouter key from {settings_path}") from exc
            if api_key:
                return api_key
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    def _expand_env(self, env_map: dict[str, str]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for key, value in env_map.items():
            if value == "${OPENROUTER_API_KEY}":
                resolved[key] = self._resolve_openrouter_api_key()
            else:
                resolved[key] = value
        return resolved

    def _redact_secret(self, value: object, secret: str) -> object:
        if not secret:
            return value
        if isinstance(value, str):
            return value.replace(secret, "<redacted>")
        if isinstance(value, list):
            return [self._redact_secret(item, secret) for item in value]
        if isinstance(value, dict):
            return {key: self._redact_secret(item, secret) for key, item in value.items()}
        return value

    def _write_patch(self, baseline_dir: Path, target_dir: Path, output_path: Path) -> None:
        proc = subprocess.run(
            ["git", "--no-pager", "diff", "--no-index", str(baseline_dir), str(target_dir)],
            capture_output=True,
            check=False,
        )
        output_path.write_bytes(proc.stdout or b"")

    def _run_subprocess(
        self,
        command: list[str],
        cwd: Path,
        env: dict[str, str],
        stdout_path: Path,
        stderr_path: Path,
        timeout_seconds: int,
    ) -> tuple[int | None, float | None, str | None]:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            try:
                proc = subprocess.run(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return None, time.monotonic() - start, "timeout"
        return proc.returncode, time.monotonic() - start, None

    def _docker_preflight(self, run_spec: RunSpec, paths: dict[str, Path]) -> RunResult | None:
        command = ["docker", "ps", "--format", "{{.ID}}"]
        proc = subprocess.run(
            command,
            cwd=self.repo_root,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return None
        compatibility = CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            adapter_name=run_spec.agent_id,
            native_supported=True,
        )
        return self._build_infra_error_result(
            run_spec,
            compatibility,
            check_name="docker_preflight",
            artifact_path=run_spec.run_root / "checks" / "docker_preflight.json",
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def _compose_command(self, workspace_dir: Path, *args: str) -> list[str]:
        return [
            "docker",
            "compose",
            "-f",
            str(workspace_dir / "upstream" / "mediacms" / "docker-compose-dev.yaml"),
            "-f",
            str(workspace_dir / "docker" / "compose.benchmark.yaml"),
            *args,
        ]

    def _compose_cwd(self, workspace_dir: Path) -> Path:
        return workspace_dir / "upstream" / "mediacms"

    def _compose_env(self, run_spec: RunSpec, workspace_dir: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["COMPOSE_PROJECT_NAME"] = run_spec.run_id.replace("-", "")
        env["PWD"] = str(workspace_dir / "upstream" / "mediacms")
        return env

    def _app_python(self) -> str:
        return "/home/mediacms.io/bin/python"

    def _app_pytest(self) -> str:
        return "/home/mediacms.io/bin/pytest"

    def _run_check(
        self,
        name: str,
        command: list[str],
        cwd: Path,
        env: dict[str, str],
        output_path: Path,
    ) -> dict[str, object]:
        proc = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            check=False,
        )
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
        output_path.write_text(
            json.dumps(
                {
                    "command": command,
                    "returncode": proc.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return {
            "name": name,
            "passed": proc.returncode == 0,
            "artifact": str(output_path),
            "returncode": proc.returncode,
        }

    def _discover_targeted_tests(self, workspace_dir: Path) -> list[str]:
        app_root = workspace_dir / "upstream" / "mediacms"
        candidates: list[str] = []
        for path in sorted(app_root.rglob("test*content_warning*.py")):
            if "tests" not in path.parts:
                continue
            candidates.append(path.relative_to(app_root).as_posix())
        if candidates:
            return candidates

        for path in sorted(app_root.rglob("test*.py")):
            if "tests" not in path.parts:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "content_warning" in content:
                candidates.append(path.relative_to(app_root).as_posix())
        return candidates

    def _seed_browser_media(self, run_spec: RunSpec, workspace_dir: Path) -> tuple[bool, int | None, str]:
        # Seed a deterministic demo user/media pair for local benchmark browser verification only.
        seed_script = (
            "from django.core.files import File; "
            "from files.models import Media; "
            "from files.tests import create_account; "
            "user = create_account(username='benchmark_user', email='benchmark_user@example.com', password='benchmark-pass'); "
            "media = Media.objects.filter(title='Playwright Content Warning Demo').first(); "
            "fh = open('fixtures/test_image2.jpg', 'rb'); "
            "media = media or Media(title='Playwright Content Warning Demo', description='Playwright demo item', "
            "user=user, state='public', encoding_status='success', is_reviewed=True, listable=True, "
            "content_warning='adult', media_file=File(fh)); "
            "media.content_warning = 'adult'; "
            "media.save(); "
            "fh.close(); "
            "print(media.id)"
        )
        try:
            proc = subprocess.run(
                self._compose_command(
                    workspace_dir,
                    "exec",
                    "--env",
                    "TESTING=True",
                    "-T",
                    "web",
                    "sh",
                    "-lc",
                    f"cd /home/mediacms.io/mediacms && {self._app_python()} manage.py shell -c {seed_script!r}",
                ),
                cwd=self._compose_cwd(workspace_dir),
                env=self._compose_env(run_spec, workspace_dir),
                capture_output=True,
                check=False,
                timeout=self.BROWSER_COMPOSE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return (
                False,
                None,
                f"Timed out after {self.BROWSER_COMPOSE_TIMEOUT_SECONDS}s while seeding browser media",
            )
        if proc.returncode != 0:
            return False, None, (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        try:
            stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
            media_id = int(stdout.splitlines()[-1])
        except (IndexError, ValueError):
            return False, None, (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        return True, media_id, ""

    def _verify_browser_value(self, run_spec: RunSpec, workspace_dir: Path, expected_value: str) -> bool:
        verify_script = (
            "from files.models import Media; "
            "media=Media.objects.get(title='Playwright Content Warning Demo'); "
            f"assert media.content_warning == '{expected_value}'"
        )
        try:
            proc = subprocess.run(
                self._compose_command(
                    workspace_dir,
                    "exec",
                    "--env",
                    "TESTING=True",
                    "-T",
                    "web",
                    "sh",
                    "-lc",
                    f"cd /home/mediacms.io/mediacms && {self._app_python()} manage.py shell -c {verify_script!r}",
                ),
                cwd=self._compose_cwd(workspace_dir),
                env=self._compose_env(run_spec, workspace_dir),
                capture_output=True,
                check=False,
                timeout=self.BROWSER_COMPOSE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return False
        return proc.returncode == 0

    def run_acceptance(
        self,
        run_spec: RunSpec,
        workspace_dir: Path,
    ) -> list[dict[str, object]]:
        checks_dir = run_spec.run_root / "checks"
        checks_dir.mkdir(parents=True, exist_ok=True)
        env = self._compose_env(run_spec, workspace_dir)
        automated_checks: list[dict[str, object]] = []

        up_check = self._run_check(
            "environment_boot",
            self._compose_command(
                workspace_dir,
                "up",
                "-d",
                "db",
                "redis",
                "migrations",
                "web",
                "celery_worker",
                "benchmark_runner",
                "benchmark_judge",
            ),
            self._compose_cwd(workspace_dir),
            env,
            checks_dir / "environment_boot.json",
        )
        automated_checks.append(up_check)
        if not up_check["passed"]:
            return automated_checks

        targeted_paths = self._discover_targeted_tests(workspace_dir)
        if targeted_paths:
            targeted = self._run_check(
                "targeted_tests",
                self._compose_command(
                    workspace_dir,
                    "exec",
                    "--env",
                    "TESTING=True",
                    "-T",
                    "web",
                    "sh",
                    "-lc",
                    (
                        "cd /home/mediacms.io/mediacms && "
                        f"{self._app_pytest()} {' '.join(quote(path) for path in targeted_paths)} -q"
                    ),
                ),
                self._compose_cwd(workspace_dir),
                env,
                checks_dir / "targeted_tests.json",
            )
        else:
            targeted = {
                "name": "targeted_tests",
                "passed": False,
                "artifact": str(checks_dir / "targeted_tests.json"),
                "returncode": None,
                "details": "No targeted content_warning test files were discovered.",
            }
            (checks_dir / "targeted_tests.json").write_text(
                json.dumps({"discovered_paths": [], "error": targeted["details"]}, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        targeted["details"] = {"discovered_paths": targeted_paths}
        automated_checks.append(targeted)

        contract = self._run_check(
            "contract_shell",
            self._compose_command(
                workspace_dir,
                "exec",
                "--env",
                "TESTING=True",
                "-T",
                "web",
                "sh",
                "-lc",
                (
                    "cd /home/mediacms.io/mediacms && "
                    f"{self._app_python()} manage.py shell -c "
                    "\"from files.models import Media; "
                    "from files.serializers import SingleMediaSerializer; "
                    "field_names=[field.name for field in Media._meta.fields]; "
                    "serializer_fields=SingleMediaSerializer().get_fields().keys(); "
                    "assert 'content_warning' in field_names; "
                    "assert 'content_warning' in serializer_fields\""
                ),
            ),
            self._compose_cwd(workspace_dir),
            env,
            checks_dir / "contract_shell.json",
        )
        automated_checks.append(contract)

        static_ui = self._run_check(
            "ui_wiring_static",
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "forms=(Path('upstream/mediacms/files/forms.py').read_text(encoding='utf-8')); "
                    "admin=(Path('upstream/mediacms/files/admin.py').read_text(encoding='utf-8')); "
                    "assert 'content_warning' in forms; assert 'content_warning' in admin"
                ),
            ],
            workspace_dir,
            env,
            checks_dir / "ui_wiring_static.json",
        )
        automated_checks.append(static_ui)

        seeded, media_id, error_text = self._seed_browser_media(run_spec, workspace_dir)
        automated_checks.append(
            {
                "name": "browser_seed",
                "passed": seeded,
                "details": error_text,
            }
        )
        if seeded and media_id is not None:
            browser = run_admin_browser_check(workspace_dir, run_spec.run_root, media_id, web_port=run_spec.web_port)
            browser_passed = bool(browser["passed"]) and self._verify_browser_value(run_spec, workspace_dir, "violence")
            automated_checks.append(
                {
                    "name": "playwright_browser_check",
                    "passed": browser_passed,
                    "artifact": str(run_spec.run_root / "browser-check.md"),
                    "details": browser,
                }
            )

        regression = self._run_check(
            "regression_context",
            self._compose_command(
                workspace_dir,
                "exec",
                "--env",
                "TESTING=True",
                "-T",
                "web",
                "sh",
                "-lc",
                f"cd /home/mediacms.io/mediacms && {self._app_pytest()} tests/api/test_media_listings.py -q",
            ),
            self._compose_cwd(workspace_dir),
            env,
            checks_dir / "regression_context.json",
        )
        automated_checks.append(regression)
        return automated_checks

    def teardown_workspace(self, run_spec: RunSpec, workspace_dir: Path) -> None:
        subprocess.run(
            self._compose_command(workspace_dir, "down", "-v", "--remove-orphans"),
            cwd=self._compose_cwd(workspace_dir),
            env=self._compose_env(run_spec, workspace_dir),
            text=True,
            capture_output=True,
            check=False,
        )

    def run_attempt(self, run_spec: RunSpec) -> RunResult:
        run_spec.run_root.mkdir(parents=True, exist_ok=True)
        paths = self._result_paths(run_spec)
        task = self.load_task(run_spec.task_id)
        adapter = self.adapter_for(run_spec.agent_id)
        compatibility = adapter.preflight(run_spec)
        write_preflight_json(
            compatibility.status.value,
            compatibility.to_dict(),
            paths["preflight"],
        )
        if compatibility.status != CompatibilityStatus.COMPATIBLE:
            result = self._build_incompatible_result(run_spec, compatibility)
            self._render_run_artifacts(result)
            return result

        docker_preflight = self._docker_preflight(run_spec, paths)
        if docker_preflight is not None:
            self._render_run_artifacts(docker_preflight)
            return docker_preflight

        home_dir = self._agent_home(run_spec)
        home_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir = self.prepare_workspace(run_spec, adapter.git_repo_root(run_spec.run_root / "workspace"))
        try:
            adapter.prepare_workspace(run_spec, workspace_dir, home_dir)
            prompt = self.build_prompt(task)
            api_key = self._resolve_openrouter_api_key()

            env = os.environ.copy()
            env.update(self._expand_env(dict(adapter.runtime_env(run_spec, workspace_dir, home_dir))))

            auth_commands: list[list[str]] = []
            if hasattr(adapter, "build_auth_command"):
                auth_commands.append(adapter.build_auth_command(run_spec, home_dir, api_key))
            auth_commands.extend(adapter.auth_commands(run_spec, workspace_dir, home_dir, api_key))

            if auth_commands:
                auth_events: list[dict[str, object]] = []
                auth_failed = False
                auth_exit_code: int | None = None
                for index, auth_command in enumerate(auth_commands, start=1):
                    auth_proc = subprocess.run(
                        auth_command,
                        cwd=adapter.auth_cwd(workspace_dir, home_dir),
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    auth_events.append(
                        {
                            "step": index,
                            "command": self._redact_secret(auth_command, api_key),
                            "returncode": auth_proc.returncode,
                            "stdout": self._redact_secret(auth_proc.stdout, api_key),
                            "stderr": self._redact_secret(auth_proc.stderr, api_key),
                        }
                    )
                    if auth_proc.returncode != 0:
                        auth_failed = True
                        auth_exit_code = auth_proc.returncode
                        break

                (run_spec.run_root / "auth.log").write_text(
                    json.dumps(auth_events, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                if auth_failed:
                    result = RunResult(
                        run_spec=run_spec,
                        compatibility=compatibility,
                        status=RunStatus.FAILED,
                        exit_code=auth_exit_code,
                        duration_seconds=0.0,
                        stdout_path=run_spec.run_root / "auth.log",
                        stderr_path=None,
                        patch_path=None,
                        scores=ScoreCard(
                            task_solved=0,
                            reliability=None,
                            quality=None,
                            speed_cost=None,
                            pending_axes=["reliability", "quality", "speed/cost"],
                        ),
                        automated_checks=[{"name": "auth_setup", "passed": False}],
                        manual_review={"status": "pending"},
                        actual_provider=run_spec.provider,
                        actual_model=run_spec.model,
                        run_metadata={},
                    )
                    self._render_run_artifacts(result)
                    return result

            command = adapter.build_command(run_spec, prompt, workspace_dir)
            exit_code, duration_seconds, special_status = self._run_subprocess(
                command=command,
                cwd=adapter.command_cwd(workspace_dir),
                env=env,
                stdout_path=paths["stdout"],
                stderr_path=paths["stderr"],
                timeout_seconds=run_spec.timeout_seconds,
            )
            run_metadata = adapter.finalize_run(
                run_spec=run_spec,
                workspace_dir=workspace_dir,
                home_dir=home_dir,
                env=env,
                stdout_path=paths["stdout"],
                stderr_path=paths["stderr"],
            )
            self._write_patch(
                self.repo_root / "upstream" / "mediacms",
                workspace_dir / "upstream" / "mediacms",
                paths["patch"],
            )

            automated_checks: list[dict[str, object]] = []
            status = RunStatus.SUCCESS
            if special_status == "timeout":
                status = RunStatus.TIMEOUT
            elif exit_code not in (0, None):
                status = RunStatus.FAILED

            if status != RunStatus.TIMEOUT:
                automated_checks = self.run_acceptance(run_spec, workspace_dir)
                if not all(item.get("passed") for item in automated_checks if item["name"] != "regression_context"):
                    status = RunStatus.FAILED

            scores = score_v1(automated_checks, duration_seconds)
            result = RunResult(
                run_spec=run_spec,
                compatibility=compatibility,
                status=status,
                exit_code=exit_code,
                duration_seconds=duration_seconds,
                stdout_path=paths["stdout"],
                stderr_path=paths["stderr"],
                patch_path=paths["patch"],
                scores=scores,
                automated_checks=automated_checks,
                manual_review={"status": "pending"},
                actual_provider=run_spec.provider,
                actual_model=run_spec.model,
                run_metadata=run_metadata,
            )
            self._render_run_artifacts(result)
            return result
        finally:
            self.teardown_workspace(run_spec, workspace_dir)

    def write_cohort_report(self, results: list[RunResult], output_dir: Path) -> Path:
        executed = [item for item in results if item.status != RunStatus.INCOMPATIBLE]
        incompatible = [item for item in results if item.status == RunStatus.INCOMPATIBLE]
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "summary.md"
        report_path.write_text(render_cohort_summary(executed, incompatible), encoding="utf-8")
        return report_path
