from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .paths import app_data_dir


@dataclass(slots=True)
class UiSettings:
    theme: str = "system"
    account_header_state: str = ""


class SettingsStore:
    VALID_THEMES = {"system", "light", "dark"}

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "settings.json")
        self.data = self._load()

    def _load(self) -> UiSettings:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return UiSettings()
        if not isinstance(raw, dict):
            return UiSettings()
        theme = str(raw.get("theme") or "system")
        if theme not in self.VALID_THEMES:
            theme = "system"
        return UiSettings(
            theme=theme,
            account_header_state=str(raw.get("account_header_state") or ""),
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "theme": self.data.theme,
            "account_header_state": self.data.account_header_state,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def set_theme(self, theme: str) -> None:
        if theme not in self.VALID_THEMES:
            raise ValueError(theme)
        self.data.theme = theme
        self.save()

    def set_account_header_state(self, state: str) -> None:
        self.data.account_header_state = state
        self.save()
