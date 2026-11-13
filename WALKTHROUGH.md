# Video and interview guide (not required in the repo, keep for yourself)

## Request flow (explain this in the code walkthrough)
Browser form -> `fetch()` in `static/app.js` -> Flask route in `app.py`
-> `validators.validate_patient()` -> `database.find_duplicate()`
-> `ai_service.generate_remarks()` -> `database.create_patient()` -> JSON back -> table refreshes.

## Why 4 of the 10 entries fail
| Test | Error shown | Why | How it is detected |
|---|---|---|---|
| 2 John Hunter | Invalid email | `hunter@gmail` has no domain extension (.com etc.) | `EMAIL_RE` regex in `validators.py` |
| 4 Peter Larry | Date does not exist | November has 30 days, so 31.11.2001 is impossible | `datetime.strptime` checks the real calendar |
| 6 Robyn Pears | Email already exists | Exact duplicate of Test 1 | `find_duplicate()` in `database.py`, backed by UNIQUE constraints in the table |
| 8 Kris Wu | Future DOB and invalid email | 2030 is after today, and `Kris.wu.gmail.com` has no `@` | `dob > date.today()` check and `EMAIL_RE` |

Saved: tests 1, 3, 5, 7, 9, 10 (6 records). Test 4's email also has a capital L, which would be lowercased on save.

## Suggested video order (about 6-8 minutes)
1. Show the app and the folder structure in VS Code.
2. Add tests 1 to 10 using the form (the dropdown fills the fields, you press Save). Pause on each error and explain it using the table above.
3. Read: show the 6 saved records and their AI remarks.
4. Edit: change one record's email to gokul@infocare.com.
5. Delete: delete one record, show the list again.
6. Code walkthrough: `ai_service.py` (prompt, API call, fallback), then `app.py` (routes), `validators.py`, `database.py`.
7. Show the GitHub repo and point out `.env` is not committed.

## Likely interview questions
- Why SQLite? No server needed, built into Python, enough for this scale.
- Why parameterised queries (`?`)? They prevent SQL injection.
- Why validate on the server when the browser could do it? Anyone can call the API directly, so the server must be the source of truth.
- What if the AI API is down? `generate_remarks` catches the error and uses rule-based remarks.
- Why are API keys in `.env`? So they never get committed to GitHub.
