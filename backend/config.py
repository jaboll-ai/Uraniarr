import json
from pathlib import Path
import os

class ConfigManager:
    """
    A simple JSON-backed config manager that exposes settings as attributes.
    Any attribute set/get (other than internal properties) is mapped to a key in the JSON file.
    """

    _SPECIAL_ATTRS = {"config_dir", "config_file", "_data", "_save"}
    config_dir = Path(os.getenv("CONFIG_DIR", "./config"))
    config_dir.mkdir(parents=True, exist_ok=True)

    def __init__(self):
        # Set up paths without triggering __setattr__ for config data
        object.__setattr__(self, "config_file", self.config_dir / "config.json")
        # Load or initialize data
        user_data = json.loads(self.config_file.read_text(encoding="utf-8")) if self.config_file.exists() else {}
        default_data = {
            "indexer_url": {
                "value": "",
                "input_type": "text",
            },
            "indexer_apikey": {
                "value": "",
                "input_type": "password",
            },
            "downloader_url": {
                "value": "",
                "input_type": "text",
            },
            "downloader_apikey": {
                "value": "",
                "input_type": "password",
            },
            "downloader_category": {
                "value": "",
                "input_type": "text",
            },
            "data_path": {
                "value": "",
                "input_type": "text",
            },
            "import_poll_interval": {
                "value": 60,
                "input_type": "number"
            },
            "unwanted_extensions": {
                "value": ".nfo,.sample,.url,.htm,.jpg,.png",
                "input_type": "text"
            },
            "playwright": {
                "value": True,
                "input_type": "checkbox"
            },
            "skip_cache": {
                "value": False,
                "input_type": "checkbox"
            },
            "known_bundles": {
                "value": "Krimi Box,Krimi-Box",
                "input_type": "text"
            }
            # "devTest": {
            #     "value": "",
            #     "input_type": "select",
            #     "options": [
            #         "Development",
            #         "Staging",
            #         "Production",
            #     ],
            # },
        }
        data = {**default_data, **user_data}
        object.__setattr__(self, "_data", data)

    def _save(self) -> None:
        """Persist the in-memory data to the JSON file."""
        self.config_file.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def __getattr__(self, name: str):
        """
        Called when attribute lookup doesn't find the name in the usual places.
        We forward it to the internal data dict.
        """
        if name in self._data:
            return self._data[name]["value"]
        return None

    def __setattr__(self, name: str, value) -> None:
        """
        Called for attribute assignment.  Non-special attributes are saved in data and persisted.
        """
        if name in self._SPECIAL_ATTRS or name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            # Set in config data and persist
            self._data[name]["value"] = value
            self._save()

    def get(self):
        return self._data

    def __repr__(self) -> str:
        return f"<ConfigManager {self._data}>"
