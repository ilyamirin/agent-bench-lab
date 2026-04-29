from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from benchmark_lab.adapters import build_adapter_registry
from benchmark_lab.adapters.yulya_zig import YulyaZigAdapter
from benchmark_lab.models import CompatibilityStatus, RunSpec


class YulyaZigAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="yulya-zig-adapter-"))
        self.run_spec = RunSpec(
            agent_id="yulya-zig",
            task_id="simple_content_warning",
            attempt=1,
            provider="openrouter",
            model="qwen/qwen3.6-plus",
            workspace_snapshot_ref="mediacms@deadbeef",
            timeout_seconds=900,
            repo_root=self.temp_dir,
        )
        self.built_binary = self.temp_dir / "native" / "yulya-zig" / "zig-out" / "bin" / "yulya-zig"
        self.built_binary.parent.mkdir(parents=True, exist_ok=True)
        self.built_binary.write_text("", encoding="utf-8")

    def test_preflight_accepts_valid_runtime(self) -> None:
        adapter = YulyaZigAdapter(repo_root=self.temp_dir, zig_binary="/bin/sh", built_binary=self.built_binary)
        with (
            patch("benchmark_lab.adapters.yulya_zig.shutil.which", side_effect=lambda name: "/usr/bin/docker" if name == "docker" else None),
            patch("benchmark_lab.adapters.yulya_zig._resolve_playwright_wrapper", return_value=Path("/tmp/playwright_cli.sh")),
            patch.object(YulyaZigAdapter, "_version", return_value="yulya-zig 0.1.0"),
        ):
            result = adapter.preflight(self.run_spec)

        self.assertEqual(result.status, CompatibilityStatus.COMPATIBLE)
        self.assertEqual(result.details["binary"], str(self.built_binary))

    def test_preflight_rejects_wrong_provider(self) -> None:
        adapter = YulyaZigAdapter(repo_root=self.temp_dir, zig_binary="/bin/sh", built_binary=self.built_binary)
        result = adapter.preflight(replace(self.run_spec, provider="openai"))
        self.assertEqual(result.status, CompatibilityStatus.INCOMPATIBLE_PROVIDER)

    def test_preflight_fails_when_built_binary_missing(self) -> None:
        missing_binary = self.temp_dir / "missing" / "yulya-zig"
        adapter = YulyaZigAdapter(repo_root=self.temp_dir, zig_binary="/bin/sh", built_binary=missing_binary)
        result = adapter.preflight(self.run_spec)
        self.assertEqual(result.status, CompatibilityStatus.INCOMPATIBLE_UNKNOWN)
        self.assertIn("not built", result.details["reason"])

    def test_build_command_uses_app_root(self) -> None:
        adapter = YulyaZigAdapter(repo_root=self.temp_dir, zig_binary="/bin/sh", built_binary=self.built_binary)
        workspace_dir = self.temp_dir / "workspace"
        command = adapter.build_command(self.run_spec, "hello", workspace_dir)
        self.assertEqual(command[0], str(self.built_binary))
        self.assertIn("--workspace", command)
        self.assertIn("--json", command)
        self.assertEqual(adapter.command_cwd(workspace_dir), workspace_dir / "upstream" / "mediacms")

    def test_registry_contains_yulya_zig_adapter(self) -> None:
        registry = build_adapter_registry()
        self.assertIn("yulya-zig", registry)
        self.assertIsInstance(registry["yulya-zig"], YulyaZigAdapter)
