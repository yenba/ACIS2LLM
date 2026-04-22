"""Configuration management for acis2llm."""

import os
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".acis2llm"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

ENV_OVERRIDES = {
    "endpoint_url": "ACIS2LLM_ENDPOINT",
    "api_key": "ACIS2LLM_API_KEY",
    "model": "ACIS2LLM_MODEL",
}


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config(flag_overrides=None):
    """Load configuration from file, with optional flag overrides.

    Args:
        flag_overrides: dict with keys endpoint_url, api_key, model

    Returns:
        dict with endpoint_url, api_key, model, or None if not configured.
    """
    if flag_overrides is None:
        flag_overrides = {}

    if not CONFIG_FILE.exists():
        return None

    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)

    if config is None:
        return None

    result = {}
    for key in ("endpoint_url", "api_key", "model"):
        # Flag overrides take highest priority
        if key in flag_overrides and flag_overrides[key] is not None:
            result[key] = flag_overrides[key]
        # Env vars take next priority
        elif ENV_OVERRIDES.get(key) and os.environ.get(ENV_OVERRIDES[key]):
            result[key] = os.environ[ENV_OVERRIDES[key]]
        # Config file values last
        elif key in config and config[key]:
            result[key] = config[key]
        else:
            result[key] = ""

    return result


def save_config(config_dict):
    """Save configuration to file.

    Args:
        config_dict: dict with keys endpoint_url, api_key, model
    """
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False)


def reset_config():
    """Remove configuration file."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
