"""Configuration management for the application."""

import json
from pathlib import Path
from typing import List, Dict, Any
from app.logger import setup_logger
import os

logger = setup_logger()

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gdrive-backup-manager"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "folders": [],
    "settings": {
        "rclone_remote": "gdrive",
        "backup_root": "Backups"
    }
}

class ConfigManager:
    """Handles loading, saving, and accessing application configuration."""

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self) -> None:
        """Creates the configuration directory if it doesn't exist."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Loads configuration from disk, or creates default if missing."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info("Configuration loaded from %s", CONFIG_FILE)
                
                # Ensure 'folders' key exists even if loading an old config
                if "folders" not in self._config:
                    self._config["folders"] = []
                    self.save()
                    
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Failed to load config: %s. Using defaults.", e)
                self._config = DEFAULT_CONFIG.copy()
                self.save()
        else:
            logger.info("No config found. Initializing defaults.")
            self._config = DEFAULT_CONFIG.copy()
            self.save()

    def save(self) -> None:
        """Saves the current configuration to disk."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            logger.info("Configuration saved to %s", CONFIG_FILE)
        except IOError as e:
            logger.error("Failed to save config: %s", e)

    @property
    def folders(self) -> List[Dict[str, str]]:
        """Returns the list of configured backup folders."""
        return self._config.get("folders", [])

    @folders.setter
    def folders(self, value: List[Dict[str, str]]) -> None:
        """Updates the folder list and saves."""
        self._config["folders"] = value
        self.save()

    @property
    def settings(self) -> Dict[str, Any]:
        """Returns application settings."""
        return self._config.get("settings", DEFAULT_CONFIG["settings"])