"""Safely inspect configuration variables without logging or printing values."""

import os
from pathlib import Path
from dotenv import load_dotenv

env_file = Path(".env")
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

keys = [
    "XAI_API_KEY",
    "FOOTBALL_DATA_API_KEY",
    "API_FOOTBALL_KEY",
    "THE_ODDS_API_KEY",
    "AGENTVERSE_API_KEY",
    "AGENT_SEED",
]

print("=== Safe Credential Inspection ===")
for k in keys:
    val = os.getenv(k, "").strip()
    is_valid = bool(val and not val.startswith("your_") and val != "<secret>" and len(val) > 3)
    status = "CONFIGURED" if is_valid else "NOT_CONFIGURED"
    print(f"{k}: {status}")
