from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from benchmark_lab.workspace import create_workspace_snapshot


class WorkspaceSnapshotTest(unittest.TestCase):
    def test_snapshot_copies_repo_but_skips_git_agents_and_venv(self) -> None:
        source_root = Path(tempfile.mkdtemp(prefix="snapshot-source-"))
        target_root = Path(tempfile.mkdtemp(prefix="snapshot-target-"))

        (source_root / ".git").mkdir()
        (source_root / ".agents").mkdir()
        (source_root / ".venv").mkdir()
        (source_root / "runs").mkdir()
        (source_root / "upstream" / "mediacms" / ".git").mkdir(parents=True)
        (source_root / "upstream" / "mediacms" / "README.md").parent.mkdir(parents=True, exist_ok=True)
        (source_root / "upstream" / "mediacms" / "README.md").write_text("hello", encoding="utf-8")
        (source_root / "README.md").write_text("root", encoding="utf-8")

        snapshot_dir = create_workspace_snapshot(source_root, target_root / "workspace")

        self.assertTrue((snapshot_dir / "README.md").exists())
        self.assertTrue((snapshot_dir / "upstream" / "mediacms" / "README.md").exists())
        self.assertFalse((snapshot_dir / ".git").exists())
        self.assertFalse((snapshot_dir / ".agents").exists())
        self.assertFalse((snapshot_dir / ".venv").exists())
        self.assertFalse((snapshot_dir / "runs").exists())
        self.assertFalse((snapshot_dir / "upstream" / "mediacms" / ".git").exists())


if __name__ == "__main__":
    unittest.main()
