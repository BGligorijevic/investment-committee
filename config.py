import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__) / ".env"


class bcolors:
    ORANGE = "\033[33m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    RESET = "\033[0m"


# Load the .env file from the explicit path.
load_dotenv(dotenv_path=env_path)

print(f"\n{bcolors.ORANGE}{'='*30} CONFIG {'='*30}")

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
print(f"Model: '{MODEL}'")

print(f"{'='*68}{bcolors.RESET}\n")
