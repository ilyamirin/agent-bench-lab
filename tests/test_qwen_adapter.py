from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from benchmark_lab.adapters.qwen_code import QwenCodeAdapter
from benchmark_lab.models import CompatibilityStatus, RunSpec


class QwenCodeAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(tempfile.mkdtemp(prefix="benchmark-qwen-adapter-"))
        self.run_spec = RunSpec(
            agent_id="qwen-code",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=self.repo_root,
        )

    def test_settings_are_generated_for_openrouter_and_exact_model(self) -> None:
        adapter = QwenCodeAdapter()

        settings = adapter.build_settings(self.run_spec)

        self.assertEqual(settings["security"]["auth"]["selectedType"], "openai")
        self.assertEqual(settings["model"]["name"], "qwen/qwen3.6-plus")
        provider = settings["modelProviders"]["openai"][0]
        self.assertEqual(provider["id"], "qwen/qwen3.6-plus")
        self.assertEqual(provider["envKey"], "OPENROUTER_API_KEY")
        self.assertEqual(provider["baseUrl"], "https://openrouter.ai/api/v1")

    def test_prepare_workspace_writes_settings_file(self) -> None:
        adapter = QwenCodeAdapter(binary_path="/opt/homebrew/bin/qwen")
        workspace_dir = self.repo_root / "workspace"
        home_dir = self.repo_root / "home"
        workspace_dir.mkdir()
        home_dir.mkdir()

        metadata = adapter.prepare_workspace(self.run_spec, workspace_dir, home_dir)

        settings_path = workspace_dir / ".qwen" / "settings.json"
        self.assertEqual(metadata["settings_path"], str(settings_path))
        self.assertTrue(settings_path.exists())

    def test_headless_command_uses_native_json_mode(self) -> None:
        adapter = QwenCodeAdapter(binary_path="/opt/homebrew/bin/qwen")

        command = adapter.build_command(
            run_spec=self.run_spec,
            prompt="Add a content_warning field",
            workspace_dir=self.repo_root,
        )

        self.assertEqual(command[0], "/opt/homebrew/bin/qwen")
        self.assertIn("--auth-type", command)
        self.assertIn("openai", command)
        self.assertIn("--model", command)
        self.assertIn("qwen/qwen3.6-plus", command)
        self.assertIn("--output-format", command)
        self.assertIn("json", command)
        self.assertIn("--yolo", command)

    def test_preflight_reports_compatible_when_binary_is_present(self) -> None:
        adapter = QwenCodeAdapter(binary_path="/opt/homebrew/bin/qwen")

        result = adapter.preflight(self.run_spec)

        self.assertEqual(result.status, CompatibilityStatus.COMPATIBLE)
        self.assertTrue(result.native_supported)

    def test_preflight_reports_incompatible_when_binary_is_missing(self) -> None:
        adapter = QwenCodeAdapter(binary_path="/nonexistent/qwen")

        result = adapter.preflight(self.run_spec)

        self.assertEqual(result.status, CompatibilityStatus.INCOMPATIBLE_UNKNOWN)
        self.assertFalse(result.native_supported)


if __name__ == "__main__":
    unittest.main()
