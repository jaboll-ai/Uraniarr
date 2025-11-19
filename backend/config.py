import json
import os
from pathlib import Path

class ConfigManager:
    """
    A simple JSON-backed config manager that exposes settings as attributes.
    Any attribute set/get (other than internal properties) is mapped to a key in the JSON file.
    """

    _SPECIAL_ATTRS = {"config_dir", "config_file", "_data", "_save"}


    def __init__(self, config_dir: str):
        if os.getenv("DEV"):
            config_dir = Path(os.getenv("DEV")) / config_dir[1:] # DEV
        config_dir = Path(config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)
        # Set up paths without triggering __setattr__ for config data
        object.__setattr__(self, "config_dir", config_dir)
        object.__setattr__(self, "config_file", self.config_dir / "config.json")
        # Load or initialize data
        user_data = json.loads(self.config_file.read_text(encoding="utf-8")) if self.config_file.exists() else {}
        default_data = {
            "book_template": {
                "value": "{{author.name}}/{{series.name}}/{{book.position} - }{{book.name}}",
                "input_type": "text",
            },
            "audiobook_template": {
                "value": "{{author.name}}/{{series.name}}/{{book.position} - }{{book.name}}",
                "input_type": "text",
            },
            "indexers": {
                "value": [
                    {
                        "name": "Indexer",
                        "url": "https://example.com",
                        "apikey": "XXXXXXXXXXXXXXX",
                        "type": "newznab",
                        "book": True,
                        "audio": True,
                        "audio_categories": "3000",
                        "book_categories": "7100"
                    }
                ],
                "input_type": "indexer"
            },
            "downloaders": {
                "value": [],
                "input_type": "downloader"
            },
            "audio_path": {
                "value": "",
                "input_type": "text",
            },
            "book_path": {
                "value": "",
                "input_type": "text",
            },
            "import_poll_interval": {
                "value": 60,
                "input_type": "number"
            },
            "rescan_interval": {
                "value": 3600,
                "input_type": "number"
            },
            "reimport_interval": {
                "value": 3600,
                "input_type": "number"
            },
            "indexer_timeout": {
                "value": 5,
                "input_type": "number"
            },
            "audio_extensions_rating": {
                "value": ".flac,.mp3,.mkv",
                "input_type": "text"
            },
            "book_extensions": {
                "value": ".epub,.mobi,.cbr,.azw,.azw3",
                "input_type": "text"
            },
            "language": {
                "value": "ger",
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
            "ignore_safe_delete": {
                "value": False,
                "input_type": "checkbox"
            },
            "known_bundles": {
                "value": "Krimi Box,Krimi-Box,3er-Box",
                "input_type": "text"
            },
            "import_unfinished": {
                "value": False,
                "input_type": "checkbox"
            },
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
        data = default_data | user_data
        data = {k: user_data[k] if k in user_data else v for k, v in default_data.items()}
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
        r = {
            k : {
                "value": v["value"] if v["input_type"] != "password" else "*"*len(v["value"]),
                "input_type": v["input_type"]
            } for k, v in self._data.items()
        }
        return r

    def __repr__(self) -> str:
        return f"<ConfigManager {self.get()}>"
