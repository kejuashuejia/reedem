import random
import requests


def fetch_api_key_from_remote(url: str) -> str | None:
    """Fetch JSON from a URL and return a randomly selected API key.

    Supported formats:
    - { "array_simple": ["key1", "key2"] }
    - { "weighted_object": { "keys": [{"key": "k", "weight": 1}, ...] } }
    - A plain JSON array of strings

    Returns a key string or None on failure.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Simple array under key
        if isinstance(data, dict) and "array_simple" in data and isinstance(data["array_simple"], list) and data["array_simple"]:
            return random.choice(data["array_simple"])

        # Weighted object
        if isinstance(data, dict) and "weighted_object" in data and isinstance(data["weighted_object"], dict):
            keys = data["weighted_object"].get("keys", [])
            if keys:
                choices = [k.get("key") for k in keys if k.get("key")]
                weights = [k.get("weight", 1) for k in keys if k.get("key")]
                if choices and weights and len(choices) == len(weights):
                    return random.choices(choices, weights=weights, k=1)[0]

        # If JSON is just a list
        if isinstance(data, list) and data:
            return random.choice(data)

        return None
    except Exception:
        return None

REMOTE_API_KEYS_URL = "https://pastebin.com/raw/ex7xPMqc"


def ensure_api_key(remote_url: str | None = None, local_path: str = "apikey.anomali") -> str:
    """Ensure an API key is available.

    Order:
    1. If local_path exists and contains a key -> return it.
    2. Attempt to fetch a key from remote_url -> if found, write to local_path and return.
    3. Prompt user interactively for API key, write to local_path and return.

    This centralizes the logic so callers (main/master) can be concise.
    """
    import os
    from app.util import get_api_key

    # Default remote URL moved here for central configuration
    REMOTE_API_KEYS_URL = "https://pastebin.com/raw/ex7xPMqc"

    if not remote_url:
        remote_url = REMOTE_API_KEYS_URL

    # 1) Local file
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                key = f.read().strip()
            if key:
                return key
        except Exception:
            pass

    # 2) Remote fetch
    remote_key = fetch_api_key_from_remote(remote_url)
    if remote_key:
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(remote_key)
        except Exception:
            pass
        return remote_key

    # 3) Interactive fallback via get_api_key (saves to .env). Also write to local_path.
    input_key = input("GENERATE APIKEY DI BOT t.me/AnomalingeongBot\nMASUKAN APIKEY: ").strip()
    if input_key:
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(input_key)
        except Exception:
            pass
        return input_key

    # Final fallback to get_api_key()
    return get_api_key()
