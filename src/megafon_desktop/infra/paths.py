from __future__ import annotations

import os
from pathlib import Path


def app_data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = root / "MegaFonDesktop"
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "megafon-desktop.db"


def secrets_dir() -> Path:
    path = app_data_dir() / "secrets"
    path.mkdir(parents=True, exist_ok=True)
    return path
