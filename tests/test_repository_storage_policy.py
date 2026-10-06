from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_repository_storage_policy() -> None:
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "scripts/check_repository_storage.py"],
        cwd=root,
        check=True,
    )
