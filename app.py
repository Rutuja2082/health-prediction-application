"""Flask application: serves the web page and a JSON REST API for patient records.

Routes
  GET    /                      web interface
  GET    /api/patients          list all records
  POST   /api/patients          create (validate -> AI remarks -> save)
  PUT    /api/patients/<id>     update (AI remarks regenerated only if blood values changed)
  DELETE /api/patients/<id>     delete
"""
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

import ai_service  # noqa: E402  (imported after load_dotenv so env vars are available)
import database  # noqa: E402
from validators import calculate_age, parse_dob, validate_patient  # noqa: E402

app = Flask(__name__)
database.init_db()


def _prepare(data, exclude_id=None):
    """Validate and duplicate-check. Returns (clean, errors)."""
    clean, errors = validate_patient(data or {})
    if not errors:
        dup = database.find_duplicate(clean["full_name"], clean["dob"], clean["email"], exclude_id)
        if dup:
            errors[dup[0]] = dup[1]
    return clean, errors


def _remarks_for(clean):
    age = calculate_age(parse_dob(clean["dob"]))
    text, _source = ai_service.generate_remarks(age, clean["glucose"], clean["haemoglobin"], clean["cholesterol"])
    return text


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/patients")
def list_all():
    return jsonify(database.list_patients())


@app.post("/api/patients")
def create():
    clean, errors = _prepare(request.get_json(silent=True))
    if errors:
        return jsonify({"errors": errors}), 400
    clean["remarks"] = _remarks_for(clean)
    clean["id"] = database.create_patient(clean)
    return jsonify(clean), 201


@app.put("/api/patients/<int:patient_id>")
def update(patient_id):
    existing = database.get_patient(patient_id)
    if not existing:
        return jsonify({"errors": {"general": "Record not found."}}), 404
    clean, errors = _prepare(request.get_json(silent=True), exclude_id=patient_id)
    if errors:
        return jsonify({"errors": errors}), 400

    values_changed = any(
        float(existing[k]) != clean[k] for k in ("glucose", "haemoglobin", "cholesterol")
    ) or existing["dob"] != clean["dob"]
    clean["remarks"] = _remarks_for(clean) if values_changed else existing["remarks"]

    database.update_patient(patient_id, clean)
    clean["id"] = patient_id
    return jsonify(clean)


@app.delete("/api/patients/<int:patient_id>")
def delete(patient_id):
    if not database.delete_patient(patient_id):
        return jsonify({"errors": {"general": "Record not found."}}), 404
    return jsonify({"deleted": patient_id})


if __name__ == "__main__":
    app.run(debug=True)
