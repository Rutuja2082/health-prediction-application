"""Input validation for patient records.

validate_patient() returns (clean_data, errors). If `errors` is empty the data is
safe to store. Each error is keyed by field name so the UI can show it beside the field.
"""
import re
from datetime import date, datetime

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,99}$")

# Plausible human ranges (reject typos, not diagnoses)
LIMITS = {
    "glucose": (20, 800, "mg/dL"),
    "haemoglobin": (3, 25, "g/dL"),
    "cholesterol": (50, 600, "mg/dL"),
}


def parse_dob(text):
    """Accept dd/mm/yyyy, dd.mm.yyyy or dd-mm-yyyy. Returns a date or raises ValueError."""
    normalised = text.strip().replace(".", "/").replace("-", "/")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", normalised):
        raise ValueError("format")
    # strptime checks the real calendar, so 31/11/2001 is rejected
    return datetime.strptime(normalised, "%d/%m/%Y").date()


def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def validate_patient(data):
    errors, clean = {}, {}

    name = " ".join(str(data.get("full_name", "")).split())
    if not name:
        errors["full_name"] = "Full name is required."
    elif not NAME_RE.match(name):
        errors["full_name"] = "Use letters, spaces, apostrophes, dots or hyphens only (2-100 characters)."
    else:
        clean["full_name"] = name

    dob_text = str(data.get("dob", "")).strip()
    if not dob_text:
        errors["dob"] = "Date of birth is required."
    else:
        try:
            dob = parse_dob(dob_text)
            if dob > date.today():
                errors["dob"] = "Date of birth cannot be in the future."
            elif calculate_age(dob) > 120:
                errors["dob"] = "Date of birth is more than 120 years ago."
            else:
                clean["dob"] = dob.strftime("%d/%m/%Y")
        except ValueError as exc:
            if str(exc) == "format":
                errors["dob"] = "Use the format dd/mm/yyyy."
            else:
                errors["dob"] = "This date does not exist in the calendar."

    email = str(data.get("email", "")).strip().lower()
    if not email:
        errors["email"] = "Email address is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address, for example name@example.com."
    else:
        clean["email"] = email

    for field, (low, high, unit) in LIMITS.items():
        raw = str(data.get(field, "")).strip()
        label = field.capitalize()
        if raw == "":
            errors[field] = f"{label} is required."
            continue
        try:
            value = float(raw)
        except ValueError:
            errors[field] = f"{label} must be a number."
            continue
        if not low <= value <= high:
            errors[field] = f"{label} must be between {low} and {high} {unit}."
        else:
            clean[field] = value

    return clean, errors
