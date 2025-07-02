import json
from pathlib import Path

class ConfigManager:
    """
    A simple JSON-backed config manager that exposes settings as attributes.
    Any attribute set/get (other than internal properties) is mapped to a key in the JSON file.
    """
    _SPECIAL_ATTRS = {"config_dir", "config_file", "_data", "_save"}

    def __init__(self, config_folder: Path = Path('.') / '.config', filename: str = 'config.json'):
        # Set up paths without triggering __setattr__ for config data
        object.__setattr__(self, 'config_dir', config_folder)
        object.__setattr__(self, 'config_file', config_folder / filename)
        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Load or initialize data
        if self.config_file.exists():
            data = json.loads(self.config_file.read_text(encoding='utf-8'))
        else:
            data = {
                "indexer_path": "",
                "indexer_apikey": "",
                "downloader_path": "",
                "downloader_apikey": "",
                "devTest": False
            }
        object.__setattr__(self, '_data', data)

    def _save(self) -> None:
        """Persist the in-memory data to the JSON file."""
        self.config_file.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def __getattr__(self, name: str):
        """
        Called when attribute lookup doesn't find the name in the usual places.
        We forward it to the internal data dict.
        """
        if name in self._data:
            return self._data[name]
        return None

    def __setattr__(self, name: str, value) -> None:
        """
        Called for attribute assignment.  Non-special attributes are saved in data and persisted.
        """
        if name in self._SPECIAL_ATTRS or name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            # Set in config data and persist
            self._data[name] = value
            self._save()

    def get(self):
        return self._data

    def __repr__(self) -> str:
        return f"<ConfigManager {self._data}>"