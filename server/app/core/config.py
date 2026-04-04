import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


class Settings:
    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_file = self.base_dir / "config" / "app_config.json"
        self.api_prefix = "/api"
        self.api_title = "Surfer Map Generator API"
        self.api_version = "1.0.0"
        self.raw_config: dict[str, Any] = {}
        self.reload()

    def default_config(self) -> dict[str, Any]:
        return {
            "upload_folder": "uploads",
            "output_folder": "output",
            "max_upload_mb": 30,
            "allowed_extensions": [".xls", ".xlsx", ".csv", ".txt"],
            "cors_origins": [
                "http://localhost:8080",
                "http://localhost:3000",
                "http://127.0.0.1:8080",
            ],
            "surfer": {
                "prog_id": "Surfer.Application",
                "install_dir": "E:/Application_surfer11",
                "exe_path": "",
                "clr_path": "",
                "default_colormap": "Terrain.clr",
                "visible": False,
                "screen_updating": False,
            },
        }

    def reload(self) -> None:
        file_config = self._load_config_file()
        merged = self._merge_config(self.default_config(), file_config)
        self.raw_config = merged

        self.upload_folder = self._resolve_local_path(merged.get("upload_folder", "uploads"))
        self.output_folder = self._resolve_local_path(merged.get("output_folder", "output"))
        self.max_upload_mb = int(merged.get("max_upload_mb", 30))
        self.allowed_extensions = {
            str(ext).lower() for ext in merged.get("allowed_extensions", [".xls", ".xlsx", ".csv", ".txt"])
        }

        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

        self.cors_origins = merged.get("cors_origins", [])

        surfer_config = merged.get("surfer", {})
        self.surfer_prog_id = surfer_config.get("prog_id", "Surfer.Application")
        self.surfer_exe_path = self._resolve_optional_path(surfer_config.get("exe_path", ""))
        self.surfer_install_dir = self._resolve_optional_path(surfer_config.get("install_dir", ""))
        self.surfer_default_colormap = surfer_config.get("default_colormap", "Terrain.clr")
        self.surfer_clr_path = self._resolve_surfer_clr_path(surfer_config.get("clr_path", ""))
        self.surfer_visible = bool(surfer_config.get("visible", False))
        self.surfer_screen_updating = bool(surfer_config.get("screen_updating", False))

    def update_and_persist(self, updates: dict[str, Any]) -> dict[str, Any]:
        current = self._load_config_file()
        merged = self._merge_config(self.default_config(), current)
        merged = self._merge_config(merged, updates)

        with self.config_file.open("w", encoding="utf-8") as fp:
            json.dump(merged, fp, ensure_ascii=False, indent=2)

        self.reload()
        return self.raw_config

    def _load_config_file(self) -> dict[str, Any]:
        if not self.config_file.exists():
            return {}

        with self.config_file.open("r", encoding="utf-8") as fp:
            raw = json.load(fp)

        if not isinstance(raw, dict):
            raise ValueError("Config file must be a JSON object")

        return raw

    def _merge_config(self, base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _resolve_local_path(self, path_value: str) -> Path:
        path = Path(path_value)
        if not path.is_absolute():
            path = self.base_dir / path
        return path.resolve()

    def _resolve_optional_path(self, path_value: str) -> str:
        if not path_value:
            return ""

        path = Path(path_value)
        if not path.is_absolute():
            path = self.base_dir / path
        return str(path.resolve())

    def _resolve_surfer_clr_path(self, explicit_clr_path: str) -> str:
        if explicit_clr_path:
            resolved = self._resolve_optional_path(explicit_clr_path)
            if Path(resolved).exists():
                return resolved

        candidates = []

        if self.surfer_install_dir:
            candidates.append(Path(self.surfer_install_dir) / "ColorScales" / self.surfer_default_colormap)

        if self.surfer_exe_path:
            exe_dir = Path(self.surfer_exe_path).parent
            candidates.append(exe_dir / "ColorScales" / self.surfer_default_colormap)

        candidates.append(Path("E:/Application_surfer11/ColorScales") / self.surfer_default_colormap)

        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())

        return ""


settings = Settings()