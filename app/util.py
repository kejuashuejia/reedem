import os
from dotenv import load_dotenv, find_dotenv

def save_api_key(api_key: str):
    """Saves the API key to the .env file."""
    env_file = find_dotenv()
    if not env_file:
        env_file = ".env" # Create it if it doesn't exist

    lines = []
    key_found = False
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()

    with open(env_file, "w") as f:
        for line in lines:
            if line.strip().startswith("API_KEY="):
                f.write(f'API_KEY="{api_key}"\n')
                key_found = True
            else:
                f.write(line)
        if not key_found:
            f.write(f'API_KEY="{api_key}"\n')
    
    # Reload the environment variables
    load_dotenv(override=True)

def get_api_key():
    """Gets the API key from environment variables or prompts the user."""
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("API Key not found.")
        api_key = input("Please enter your API Key: ").strip()
        if api_key:
            save_api_key(api_key)
        else:
            print("API Key cannot be empty. Exiting.")
            exit(1)
    return api_key
