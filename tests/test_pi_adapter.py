from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from benchmark_lab.adapters import build_adapter_registry
from benchmark_lab.adapters.pi import PiAdapter
from benchmark_lab.models import CompatibilityStatus, RunSpec


class PiAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(tempfile.mkdtemp(prefix="benchmark-pi-adapter-"))
        self.run_spec = RunSpec(
            agent_id="pi",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=self.repo_root,
        )

    def test_prepare_workspace_creates_pi_home_layout(self) -> None:
        adapter = PiAdapter(binary_path="/usr/local/bin/pi")
        workspace_dir = self.repo_root / "workspace"
        home_dir = self.repo_root / "home"
        workspace_dir.mkdir()
        home_dir.mkdir()

        metadata = adapter.prepare_workspace(self.run_spec, workspace_dir, home_dir)

        self.assertTrue((home_dir / ".pi" / "agent").is_dir())
        self.assertTrue((home_dir / ".pi" / "agent" / "sessions").is_dir())
        self.assertEqual(metadata["auth_path"], str(home_dir / ".pi" / "agent" / "auth.json"))
        self.assertEqual(metadata["settings_path"], str(home_dir / ".pi" / "agent" / "settings.json"))

    def test_auth_commands_write_expected_pi_files(self) -> None:
        adapter = PiAdapter(binary_path="/usr/local/bin/pi")
        workspace_dir = self.repo_root / "workspace"
        home_dir = self.repo_root / "home"
        workspace_dir.mkdir()
        home_dir.mkdir()
        adapter.prepare_workspace(self.run_spec, workspace_dir, home_dir)

        commands = adapter.auth_commands(self.run_spec, workspace_dir, home_dir, "sk-or-test")

        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0][:2], ["sh", "-lc"])
        self.assertIn(str(home_dir / ".pi" / "agent" / "auth.json"), commands[0][2])
        self.assertIn('"openrouter"', commands[0][2])
        self.assertIn('"key": "sk-or-test"', commands[0][2])
        self.assertIn("chmod 600", commands[0][2])
        self.assertIn(str(home_dir / ".pi" / "agent" / "settings.json"), commands[1][2])
        self.assertIn('"defaultModel": "qwen/qwen3.6-plus"', commands[1][2])
        self.assertIn('"quietStartup": true', commands[1][2])
        self.assertIn("chmod 600", commands[1][2])

    def test_build_command_uses_print_mode_from_app_root(self) -> None:
        adapter = PiAdapter(binary_path="/usr/local/bin/pi")
        workspace_dir = self.repo_root / "workspace"
        app_root = workspace_dir / "upstream" / "mediacms"
        app_root.mkdir(parents=True)

        command = adapter.build_command(self.run_spec, "hello world", workspace_dir)

        self.assertEqual(
            command,
            [
                "/usr/local/bin/pi",
                "--mode",
                "json",
                "--provider",
                "openrouter",
                "--model",
                "qwen/qwen3.6-plus",
                "-p",
                "hello world",
            ],
        )
        self.assertEqual(adapter.command_cwd(workspace_dir), app_root)
        self.assertEqual(adapter.git_repo_root(workspace_dir), app_root)

    def test_preflight_reports_compatible_when_binary_exists(self) -> None:
        adapter = PiAdapter(binary_path="/bin/sh")
        with patch.object(PiAdapter, "_resolved_version", return_value="0.67.2"):
            result = adapter.preflight(self.run_spec)

        self.assertEqual(result.status, CompatibilityStatus.COMPATIBLE)
        self.assertTrue(result.native_supported)
        self.assertEqual(
            result.details["execution_mode"],
            "pi --mode json --provider openrouter --model qwen/qwen3.6-plus -p",
        )
        self.assertEqual(result.details["version"], "0.67.2")

    def test_preflight_rejects_wrong_provider(self) -> None:
        adapter = PiAdapter(binary_path="/bin/sh")
        wrong = replace(self.run_spec, provider="anthropic")

        result = adapter.preflight(wrong)

        self.assertEqual(result.status, CompatibilityStatus.INCOMPATIBLE_PROVIDER)

    def test_registry_contains_pi_adapter(self) -> None:
        registry = build_adapter_registry()

        self.assertIn("pi", registry)
        self.assertIsInstance(registry["pi"], PiAdapter)


if __name__ == "__main__":
    unittest.main()
