"""
Configuration Management
Handles loading and saving CCC configuration from ~/.ccc/config.json
"""

import sys
import json
from pathlib import Path


# Configuration file paths
CONFIG_DIR = Path.home() / ".ccc"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    """
    Load CCC configuration from ~/.ccc/config.json

    Returns:
        dict: Configuration dictionary (empty dict if file doesn't exist)
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return {}


def save_config(config):
    """
    Save CCC configuration to ~/.ccc/config.json

    Args:
        config: dict with configuration settings
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}")
        sys.exit(1)


def get_config_value(key, default=None):
    """
    Get a single configuration value

    Args:
        key: Configuration key to retrieve
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key, value):
    """
    Set a single configuration value

    Args:
        key: Configuration key to set
        value: Value to set
    """
    config = load_config()
    config[key] = value
    save_config(config)
