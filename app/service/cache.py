import os
import json
import time
from typing import Any, Dict, Optional

CACHE_DIR = "cache"

def _get_cache_filepath(key: str) -> str:
    """Generates a predictable and safe file path for a given cache key."""
    # Simple sanitization to prevent directory traversal attacks
    safe_key = key.replace("..", "").replace("/", "").replace("\\", "")
    return os.path.join(CACHE_DIR, f"{safe_key}.json")

def save_to_cache(key: str, data: Any):
    """
    Saves data to a cache file with a timestamp.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    filepath = _get_cache_filepath(key)

    cache_content = {
        "timestamp": time.time(),
        "data": data
    }

    with open(filepath, 'w') as f:
        json.dump(cache_content, f)

def load_from_cache(key: str, ttl_seconds: int = 1800) -> Optional[Any]:
    """
    Loads data from a cache file if it exists and is not expired.

    Args:
        key: The key to identify the cache entry.
        ttl_seconds: Time To Live in seconds. Defaults to 1800 (30 minutes).

    Returns:
        The cached data if valid, otherwise None.
    """
    filepath = _get_cache_filepath(key)

    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, 'r') as f:
            cache_content = json.load(f)
    except (IOError, json.JSONDecodeError):
        # If file is corrupt or unreadable, treat it as a cache miss
        return None

    if 'timestamp' not in cache_content or 'data' not in cache_content:
        # Invalid cache format
        return None

    cache_age = time.time() - cache_content['timestamp']

    if cache_age > ttl_seconds:
        # Cache is expired, delete it and return miss
        try:
            os.remove(filepath)
        except OSError:
            pass # Ignore errors on deletion
        return None

    return cache_content['data']
