from __future__ import annotations

import unittest

from benchmark_lab.adapters import build_adapter_registry


class AdapterRegistryTest(unittest.TestCase):
    def test_registry_contains_expected_agents(self) -> None:
        registry = build_adapter_registry()

        self.assertIn("qwen-code", registry)
        self.assertIn("aider", registry)
        self.assertIn("cline", registry)
        self.assertIn("opencode", registry)
        self.assertIn("kilocode", registry)
        self.assertIn("openhands", registry)
        self.assertIn("codebuff", registry)
        self.assertIn("crush", registry)
        self.assertIn("hermes-agent", registry)
        self.assertIn("openclaw", registry)
