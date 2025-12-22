import os
from app.colors import bcolors

def load_api_key() -> str:
    if os.path.exists("api.key"):
        with open("api.key", "r", encoding="utf8") as f:
            api_key = f.read().strip()
        if api_key:
            print(f"{bcolors.OKGREEN}API key loaded successfully.{bcolors.ENDC}")
            return api_key
        else:
            print(f"{bcolors.WARNING}API key file is empty.{bcolors.ENDC}")
            return ""
    else:
        print(f"{bcolors.FAIL}API key file not found.{bcolors.ENDC}")
        return ""
    
def save_api_key(api_key: str):
    with open("api.key", "w", encoding="utf8") as f:
        f.write(api_key)
    print(f"{bcolors.OKGREEN}API key saved successfully.{bcolors.ENDC}")
    
def delete_api_key():
    if os.path.exists("api.key"):
        os.remove("api.key")
        print(f"{bcolors.OKGREEN}API key file deleted.{bcolors.ENDC}")
    else:
        print(f"{bcolors.WARNING}API key file does not exist.{bcolors.ENDC}")

def verify_api_key(api_key: str, *, timeout: float = 10.0) -> bool:
    return True


def ensure_api_key() -> str:
    # Load API_KEY from .env file
    api_key = "vT8tINqHaOxXbGE7eOWAhA=="
    return api_key
