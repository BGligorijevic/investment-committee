import os
from dotenv import load_dotenv
from pathlib import Path
from google.adk.models.lite_llm import LiteLlm

env_path = Path(__file__) / ".env"


class bcolors:
    ORANGE = "\033[33m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    RESET = "\033[0m"


# Load the .env file from the explicit path.
load_dotenv(dotenv_path=env_path)

print(f"\n{bcolors.ORANGE}{'='*30} CONFIG {'='*30}")

MODEL_PARAM = os.environ.get("MODEL", "gemini-2.5-flash")
MAX_DELPHI_ROUNDS = int(os.environ.get("MAX_DELPHI_ROUNDS", 3))
print(f"Model: '{MODEL_PARAM}'")
print(f"Max Delphi Rounds to loop: {MAX_DELPHI_ROUNDS}")

if MODEL_PARAM.startswith("ollama/") or "llama" in MODEL_PARAM:
    full_model_name = f"ollama_chat/{MODEL_PARAM}"
    model = LiteLlm(model=full_model_name)
else:
    model = MODEL_PARAM

print(f"{'='*68}{bcolors.RESET}\n")
