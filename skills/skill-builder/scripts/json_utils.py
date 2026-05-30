"""Shared JSON utilities for skill-builder scripts."""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def load_json(path: Path) -> Any:
    """Safely load JSON from a file, logging errors."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {path}: {e}")
        raise
    except OSError as e:
        logger.error(f"Failed to read file {path}: {e}")
        raise

def save_json(path: Path, data: Any, indent: int = 2) -> None:
    """Safely save JSON to a file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
    except OSError as e:
        logger.error(f"Failed to write JSON to {path}: {e}")
        raise
