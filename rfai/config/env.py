"""Environment loading helpers for RFAI.

Goal: make `.env` "just work" even if it uses informal formats like:

    gemini = ...
    youtube = ...

We load keys into `os.environ` and also normalize them to the names used by the
codebase (e.g. `YOUTUBE_API_KEY`, `PERPLEXITY_API_KEY`).

This module intentionally never logs secret values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple


_KEY_MAP = {
    # Common informal keys -> canonical env vars
    "gemini": "GEMINI_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "youtube": "YOUTUBE_API_KEY",
    "youtube_api_key": "YOUTUBE_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "perplexity_api_key": "PERPLEXITY_API_KEY",
    "notion": "NOTION_API_KEY",
    "notion_api_key": "NOTION_API_KEY",
    "notion_database_id": "NOTION_DATABASE_ID",
    # Ollama
    "ollama_base_url": "OLLAMA_BASE_URL",
    "ollama_model": "OLLAMA_MODEL",
    # IMDb / OMDb
    "imdb": "OMDB_API_KEY",
    "omdb": "OMDB_API_KEY",
    "omdb_api_key": "OMDB_API_KEY",
}


def _parse_env_line(line: str) -> Optional[Tuple[str, str]]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    # Allow inline comments: KEY=VALUE  # comment
    if "#" in stripped:
        before_hash = stripped.split("#", 1)[0].strip()
        if before_hash:
            stripped = before_hash

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()

    # Strip optional quotes
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    if not key:
        return None

    return key, value


def _find_dotenv() -> Optional[Path]:
    """Find a `.env` file by searching common roots."""
    explicit = os.environ.get("RFAI_ENV_FILE")
    if explicit:
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() else None

    candidates = []

    # Prefer current working directory first
    try:
        candidates.append(Path.cwd())
    except Exception:
        pass

    # Then search upwards from this file
    here = Path(__file__).resolve()
    candidates.extend([here.parent] + list(here.parents))

    seen = set()
    for base in candidates:
        if str(base) in seen:
            continue
        seen.add(str(base))

        env_path = base / ".env"
        if env_path.exists():
            return env_path

    return None


def load_env(override: bool = False) -> Dict[str, str]:
    """Load `.env` into `os.environ` and normalize keys.

    Returns a dict of keys that were set (key -> value). Values are returned to
    support debugging in code, but callers should not print them.
    """
    env_path = _find_dotenv()
    if not env_path:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("No .env file found. Create one from .env.example for API key configuration.")
        logger.info("Looking for .env in: current directory or project root")
        return {}

    try:
        raw_text = env_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}

    set_vars: Dict[str, str] = {}

    for line in raw_text.splitlines():
        parsed = _parse_env_line(line)
        if not parsed:
            continue

        key, value = parsed
        key_stripped = key.strip()

        def _set(name: str, val: str) -> None:
            if override or name not in os.environ:
                os.environ[name] = val
                set_vars[name] = val

        # Always set the raw key if it's a reasonable env var name
        if key_stripped:
            _set(key_stripped, value)

        # Normalize common informal keys
        mapped = _KEY_MAP.get(key_stripped.lower())
        if mapped:
            _set(mapped, value)

        # If they provided canonical keys but with wrong case, normalize too
        upper = key_stripped.upper()
        mapped2 = _KEY_MAP.get(upper.lower())
        if mapped2:
            _set(mapped2, value)

    return set_vars


def validate_api_keys(required_keys: list = None) -> Dict[str, bool]:
    """
    Validate that required API keys are present
    
    Args:
        required_keys: List of required key names (e.g., ['YOUTUBE_API_KEY'])
                      If None, checks all common keys
    
    Returns:
        Dict mapping key name to whether it's present and valid
    """
    if required_keys is None:
        required_keys = [
            'YOUTUBE_API_KEY',
            'PERPLEXITY_API_KEY',
            'NOTION_API_KEY',
            'OMDB_API_KEY'
        ]
    
    status = {}
    for key in required_keys:
        value = os.environ.get(key, '').strip()
        # Check if key exists and is not a placeholder
        is_valid = bool(value) and not value.startswith('your_') and value != 'None'
        status[key] = is_valid
    
    return status


def print_api_key_status():
    """Print helpful status message about API key configuration"""
    import logging
    logger = logging.getLogger(__name__)
    
    status = validate_api_keys()
    
    missing_keys = [k for k, v in status.items() if not v]
    present_keys = [k for k, v in status.items() if v]
    
    if present_keys:
        logger.info(f"✅ Configured API keys: {', '.join(present_keys)}")
    
    if missing_keys:
        logger.warning(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        logger.info("Create a .env file from .env.example and add your API keys")
        logger.info("Get keys from:")
        for key in missing_keys:
            if 'YOUTUBE' in key:
                logger.info("  - YouTube: https://console.cloud.google.com/apis/credentials")
            elif 'PERPLEXITY' in key:
                logger.info("  - Perplexity: https://www.perplexity.ai/settings/api")
            elif 'NOTION' in key:
                logger.info("  - Notion: https://www.notion.so/my-integrations")
            elif 'OMDB' in key:
                logger.info("  - OMDb/IMDb: https://www.omdbapi.com/apikey.aspx")
