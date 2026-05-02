import json
import os
import logging

class SettingsManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.default_settings = {
            "auto_pronunciation": False,
            "popup_duration_sec": 4.0,
            "dark_mode": True,
            "hotkey_enabled": True,
            "hotkey": "ctrl+shift+d",
            "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.config_path):
            logging.info("Config file not found. Creating default config.")
            self.save_settings(self.default_settings)
            return self.default_settings.copy()

        try:
            with open(self.config_path, "r") as f:
                settings = json.load(f)
                # Merge with defaults in case of missing keys
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return self.default_settings.copy()

    def save_settings(self, settings=None):
        if settings is not None:
            self.settings = settings
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def get(self, key):
        return self.settings.get(key, self.default_settings.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()
