from __future__ import annotations

import unittest
from pathlib import Path

from benchmark_lab.tasks import load_task_manifest


class TaskManifestTest(unittest.TestCase):
    def test_simple_task_manifest_is_machine_readable_and_complete(self) -> None:
        manifest = load_task_manifest(
            Path("benchmark/tasks/simple_content_warning.json")
        )

        self.assertEqual(manifest.task_id, "simple_content_warning")
        self.assertEqual(manifest.difficulty, "simple")
        self.assertIn("content_warning", manifest.instructions)
        self.assertGreaterEqual(len(manifest.acceptance_commands), 2)
        self.assertIn("docker compose", manifest.acceptance_commands[0])
        self.assertIn("reference_solution_strategy", manifest.extra)
        self.assertGreaterEqual(manifest.timeout_seconds, 600)


if __name__ == "__main__":
    unittest.main()
