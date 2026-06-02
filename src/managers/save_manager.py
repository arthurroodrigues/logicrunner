import json
import os
from copy import deepcopy
from typing import Any

from src.config import SAVE_PATH


DEFAULT_SAVE = {
    "high_score": 0,
    "max_unlocked_phase": 1,
    "completed_phases": [],
    "settings": {"music_volume": 0.7, "sfx_volume": 0.8, "fullscreen": False},
}


class SaveManager:
    def __init__(self, path: str = SAVE_PATH) -> None:
        self.path = path
        self.data = self.load()

    def load(self) -> dict[str, Any]:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self.save(deepcopy(DEFAULT_SAVE))
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                loaded = json.load(file)
        except (json.JSONDecodeError, OSError):
            loaded = deepcopy(DEFAULT_SAVE)
        data = deepcopy(DEFAULT_SAVE)
        data.update(loaded)
        data["settings"].update(loaded.get("settings", {}))
        return data

    def save(self, data: dict[str, Any] | None = None) -> None:
        if data is not None:
            self.data = data
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2, ensure_ascii=False)

    def record_run(self, score: int, unlocked_phase: int, completed_phase: int | None = None) -> None:
        self.data["high_score"] = max(self.data.get("high_score", 0), score)
        self.data["max_unlocked_phase"] = max(self.data.get("max_unlocked_phase", 1), unlocked_phase)
        if completed_phase and completed_phase not in self.data["completed_phases"]:
            self.data["completed_phases"].append(completed_phase)
            self.data["completed_phases"].sort()
        self.save()

    def reset_progress(self) -> None:
        settings = self.data.get("settings", deepcopy(DEFAULT_SAVE["settings"]))
        self.data = deepcopy(DEFAULT_SAVE)
        self.data["settings"] = settings
        self.save()
