"""Prints the Gemini models your API key can call with generateContent.
Run: python list_models.py   (reads AI_API_KEY from .env)
Copy one name (without the 'models/' prefix) into AI_MODEL in your .env file."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()
resp = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    headers={"x-goog-api-key": os.environ.get("AI_API_KEY", "")},
    params={"pageSize": 100},
    timeout=20,
)
if resp.status_code != 200:
    raise SystemExit(f"Request failed ({resp.status_code}): {resp.text[:300]}")
for model in resp.json().get("models", []):
    if "generateContent" in model.get("supportedGenerationMethods", []):
        print(model["name"].replace("models/", ""))
