from __future__ import annotations

import shutil
from pathlib import Path


ROOT_EXCLUDES = {".git", ".agents", ".venv", "runs", "postgres_data", "__pycache__"}


def create_workspace_snapshot(source_root: Path, target_root: Path) -> Path:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    if target_root.exists():
        shutil.rmtree(target_root)
    target_root.parent.mkdir(parents=True, exist_ok=True)

    def _ignore(path: str, names: list[str]) -> set[str]:
        current = Path(path)
        ignored = {name for name in names if name in ROOT_EXCLUDES}
        if current == source_root / "upstream" / "mediacms" and ".git" in names:
            ignored.add(".git")
        return ignored

    shutil.copytree(source_root, target_root, ignore=_ignore)
    return target_root

