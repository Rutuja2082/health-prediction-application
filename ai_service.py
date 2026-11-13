"""Generates the "Remarks" text from blood test values.

1. Calls an external AI API (Gemini, or any OpenAI-compatible API such as Groq/OpenAI).
2. If the call fails or no key is set, falls back to simple clinical rules so the
   application keeps working. Fallback remarks are labelled so they are never
   mistaken for AI output.

Settings come from environment variables (see .env.example). No key is stored in code.
"""
import os

import requests

TIMEOUT = 20
NOTE = "Screening estimate only, not a diagnosis."


def build_prompt(age, glucose, haemoglobin, cholesterol):
    return (
        "You are a health screening assistant. A patient aged "
        f"{age} has these blood test results: glucose {glucose} mg/dL, "
        f"haemoglobin {haemoglobin} g/dL, total cholesterol {cholesterol} mg/dL.\n"
        "In at most 2 short sentences, state the possible health condition or disease risk "
        "these values suggest (for example diabetes risk, anaemia, high cholesterol), "
        "or say the values look normal. Do not give a definite diagnosis and do not use "
        "markdown or bullet points."
    )


def _call_gemini(prompt, key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    resp = requests.post(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai_compatible(prompt, key, model, base_url):
    resp = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 150},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def rule_based_remarks(age, glucose, haemoglobin, cholesterol):
    """Fallback using common adult reference thresholds."""
    findings = []
    if glucose >= 200:
        findings.append("very high glucose, possible diabetes")
    elif glucose >= 126:
        findings.append("high glucose, possible diabetes risk")
    elif glucose >= 100:
        findings.append("raised glucose, possible pre-diabetes risk")
    elif glucose < 70:
        findings.append("low glucose, possible hypoglycaemia")

    if haemoglobin < 12:
        findings.append("low haemoglobin, possible anaemia")
    elif haemoglobin > 17.5:
        findings.append("high haemoglobin, possible polycythaemia")

    if cholesterol >= 240:
        findings.append("high cholesterol, raised heart disease risk")
    elif cholesterol >= 200:
        findings.append("borderline high cholesterol")

    if not findings:
        return "Values are within typical ranges. No obvious risk detected."
    return "Possible risks: " + "; ".join(findings) + "."


def generate_remarks(age, glucose, haemoglobin, cholesterol):
    """Return (remarks_text, source) where source is 'ai' or 'rules'."""
    provider = os.environ.get("AI_PROVIDER", "gemini").lower()
    key = os.environ.get("AI_API_KEY", "").strip()
    model = os.environ.get("AI_MODEL", "gemini-3.5-flash-lite")

    if provider != "none" and key:
        prompt = build_prompt(age, glucose, haemoglobin, cholesterol)
        try:
            if provider == "gemini":
                text = _call_gemini(prompt, key, model)
            else:
                base = os.environ.get("AI_BASE_URL", "").strip() or "https://api.openai.com/v1"
                text = _call_openai_compatible(prompt, key, model, base)
            if text:
                return f"{text} {NOTE}", "ai"
        except requests.HTTPError as exc:
            # Print the API's own explanation (wrong model, bad key, quota...) to help debugging
            detail = exc.response.text[:300] if exc.response is not None else ""
            print(f"[ai_service] AI call failed ({exc}). Details: {detail}")
        except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
            print(f"[ai_service] AI call failed, using rule-based fallback: {exc}")

    return rule_based_remarks(age, glucose, haemoglobin, cholesterol) + " (rule-based fallback) " + NOTE, "rules"
