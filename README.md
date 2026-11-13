# Blood Test Risk Records

A small web application for managing patient blood test records. When a record is saved, an external AI API reads the glucose, haemoglobin and cholesterol values and writes a short screening remark into the **Remarks** column.

**Stack:** Python 3 and Flask (backend and REST API), SQLite (storage), HTML, Bootstrap 5 and JavaScript (frontend), Google Gemini API or any OpenAI-compatible API (AI remarks).

## Features
- Create, read, update and delete patient records
- Validation on both name, date of birth (dd/mm/yyyy, real calendar date, not in the future), email format, and numeric blood values within plausible ranges
- Duplicate protection (same email, or same name and date of birth)
- AI-generated remarks, with a rule-based fallback if the API is unavailable
- Persistent storage in a local SQLite file

## Project structure
```
app.py            Flask routes and REST API
database.py       SQLite storage (all SQL queries)
validators.py     Validation rules
ai_service.py     AI API call and rule-based fallback
templates/        index.html
static/           style.css, app.js
.env.example      Template for settings (copy to .env)
```

## Setup
```bash
git clone <your-repo-url>
cd health-predictor
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```
Edit `.env` and add your own API key. Free keys: Gemini at https://aistudio.google.com/apikey or Groq at https://console.groq.com.

For Groq, use:
```
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.1-8b-instant
```
Run the app:
```bash
python app.py
```
Open http://127.0.0.1:5000

If `AI_API_KEY` is empty, or the API call fails, remarks are produced by simple reference-range rules and labelled "(rule-based fallback)".

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/patients` | List all records |
| POST | `/api/patients` | Validate, get AI remarks, save |
| PUT | `/api/patients/<id>` | Update (remarks regenerate only if blood values or DOB change) |
| DELETE | `/api/patients/<id>` | Delete |

Validation failures return HTTP 400 with `{"errors": {"field": "message"}}`.

## Notes
- Remarks are screening estimates only, not medical diagnoses.
- Haemoglobin thresholds are general adult values. Sex-specific ranges are not applied because sex is not collected.

## Troubleshooting the AI call
- **HTTP 404:** the model name in `.env` is retired or unavailable to your key. Run `python list_models.py` and copy a listed model into `AI_MODEL`. (`gemini-2.0-flash` has been shut down by Google.)
- **HTTP 400 or 403:** the API key is wrong or not enabled. Create a new key at https://aistudio.google.com/apikey.
- **HTTP 429:** free-tier rate limit. Wait a minute and retry.
- After editing `.env`, stop the app (Ctrl+C) and run `python app.py` again.
