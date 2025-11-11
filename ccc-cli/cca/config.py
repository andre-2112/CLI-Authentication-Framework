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
DEFAULT_CONFIG_FILE = Path(__file__).parent / "config.default.json"


def load_default_config():
    """
    Load default configuration from package

    Returns:
        dict: Default configuration dictionary (empty dict if file doesn't exist)
    """
    if not DEFAULT_CONFIG_FILE.exists():
        return {}

    try:
        with open(DEFAULT_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Failed to load default config: {e}")
        return {}


def load_config():
    """
    Load CCC configuration from ~/.ccc/config.json
    Falls back to default config if user config doesn't exist

    Returns:
        dict: Configuration dictionary (default config if user config doesn't exist)
    """
    # Load defaults first
    config = load_default_config()

    # Overlay user config if it exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")

    return config


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
