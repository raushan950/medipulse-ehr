"""
MediPulse Hospital & EHR - Flask Web Application & REST API
CSE494: Intelligent NoSQL Databases - Academic Task 2
"""

from flask import Flask, render_template, jsonify, request, session, redirect
from flask_cors import CORS
from datetime import datetime
import math
import os
import secrets
import json
from bson import json_util
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

from database.connection import get_database
from database.seed_data import seed_database
from services.crud_service import CRUDService
from services.aggregation_service import AggregationService

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

db = get_database()
if "patients" not in db.list_collection_names():
    seed_database(reset=False)

crud_service = CRUDService()
agg_service = AggregationService()

@app.before_request
def require_admin_session():
    public_endpoints = {"static", "auth_page", "setup_admin", "login_admin", "logout_admin"}
    if request.endpoint in public_endpoints or session.get("admin_username"):
        return None
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Admin login required."}), 401
    return redirect("/auth")

def parse_json(data):
    """Converts MongoDB BSON types to JSON serializable objects."""
    return json.loads(json_util.dumps(data))

@app.route("/")
def index():
    return render_template("index.html", admin_username=session.get("admin_username"))

@app.route("/auth")
def auth_page():
    admin_exists = get_database().admins.find_one({"_id": "primary"}) is not None
    return render_template("auth.html", setup_required=not admin_exists)

@app.route("/api/auth/setup", methods=["POST"])
def setup_admin():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = data.get("password", "")
    if len(username) < 3 or len(username) > 50:
        return jsonify({"success": False, "error": "Username must be 3 to 50 characters."}), 400
    if not isinstance(password, str) or len(password) < 12:
        return jsonify({"success": False, "error": "Password must be at least 12 characters."}), 400
    if password != data.get("password_confirm"):
        return jsonify({"success": False, "error": "Passwords do not match."}), 400

    try:
        get_database().admins.insert_one({
            "_id": "primary",
            "username": username,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now()
        })
    except DuplicateKeyError:
        return jsonify({"success": False, "error": "An admin account has already been created."}), 409

    session.clear()
    session["admin_username"] = username
    return jsonify({"success": True, "message": "Admin account created."})

@app.route("/api/auth/login", methods=["POST"])
def login_admin():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = data.get("password", "")
    admin = get_database().admins.find_one({"_id": "primary"})
    if not admin or username != admin.get("username") or not isinstance(password, str) or not check_password_hash(admin["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid username or password."}), 401

    session.clear()
    session["admin_username"] = username
    return jsonify({"success": True, "message": "Signed in."})

@app.route("/api/auth/logout", methods=["POST"])
def logout_admin():
    session.clear()
    return jsonify({"success": True})

# ==========================================
# API: SYSTEM & HEALTH
# ==========================================
@app.route("/api/system/health", methods=["GET"])
def system_health():
    try:
        db = get_database()
        db.command("ping")
        stats = {
            "status": "connected",
            "database": db.name,
            "collections": db.list_collection_names(),
            "patient_count": db.patients.count_documents({}),
            "doctor_count": db.doctors.count_documents({}),
            "encounter_count": db.encounters.count_documents({}),
            "appointment_count": db.appointments.count_documents({})
        }
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# API: AGGREGATION PIPELINES
# ==========================================
@app.route("/api/analytics/executive-kpis", methods=["GET"])
def get_executive_kpis():
    data = agg_service.get_executive_kpi_dashboard()
    return jsonify({"success": True, "data": parse_json(data)})

@app.route("/api/analytics/departments", methods=["GET"])
def get_department_analytics():
    data = agg_service.get_department_financial_analytics()
    return jsonify({"success": True, "data": parse_json(data)})

@app.route("/api/analytics/doctors", methods=["GET"])
def get_doctor_analytics():
    data = agg_service.get_doctor_performance_analytics()
    return jsonify({"success": True, "data": parse_json(data)})

@app.route("/api/analytics/medications", methods=["GET"])
def get_medication_analytics():
    top_n = request.args.get("top", default=6, type=int)
    data = agg_service.get_medication_utilization_analytics(top_n)
    return jsonify({"success": True, "data": parse_json(data)})

@app.route("/api/analytics/age-stratification", methods=["GET"])
def get_age_stratification():
    data = agg_service.get_patient_age_stratification()
    return jsonify({"success": True, "data": parse_json(data)})

# ==========================================
# API: CRUD OPERATIONS
# ==========================================
@app.route("/api/patients", methods=["GET"])
def list_patients():
    blood_group = request.args.get("blood_group")
    search_term = request.args.get("search")
    city = request.args.get("city")
    query = {}
    if search_term:
        query["$text"] = {"$search": search_term}
    if blood_group:
        query["blood_group"] = blood_group
    if city:
        query["contact.address.city"] = city
    projection = {"_id": 0}
    if search_term:
        projection["score"] = {"$meta": "textScore"}
    patients = list(get_database().patients.find(query, projection))
    if search_term:
        patients.sort(key=lambda patient: patient.get("score", 0), reverse=True)

    return jsonify({"success": True, "count": len(patients), "data": parse_json(patients)})

@app.route("/api/patients/next-id", methods=["GET"])
def get_next_patient_id():
    next_id = crud_service.get_next_patient_id()
    return jsonify({"success": True, "next_id": next_id})

@app.route("/api/encounters/next-id", methods=["GET"])
def get_next_encounter_id():
    next_id = crud_service.get_next_encounter_id()
    return jsonify({"success": True, "next_id": next_id})

@app.route("/api/patients/<patient_id>", methods=["GET"])
def get_patient_ehr(patient_id):
    ehr = crud_service.get_patient_ehr_summary(patient_id)
    return jsonify({"success": ehr.get("found", False), "data": parse_json(ehr)})

@app.route("/api/patients/<patient_id>", methods=["PATCH"])
def update_patient(patient_id):
    data = request.get_json(silent=True) or {}
    result = crud_service.update_patient(patient_id, data)
    status_code = 200 if result.get("success") else (404 if "was not found" in result.get("error", "") else 400)
    return jsonify(result), status_code

@app.route("/api/patients/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    result = crud_service.delete_patient(patient_id)
    if result.get("success"):
        return jsonify(result)
    status_code = 404 if "was not found" in result.get("error", "") else 409
    return jsonify(result), status_code

@app.route("/api/patients", methods=["POST"])
def add_patient():
    data = request.json or {}
    try:
        res = crud_service.add_patient(data)
        if res.get("success"):
            return jsonify(res), 201
        else:
            return jsonify(res), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/encounters", methods=["POST"])
def create_encounter():
    """Admit a patient (Inpatient, Outpatient, Emergency)."""
    data = request.json or {}
    res = crud_service.add_encounter(data)
    status_code = 201 if res.get("success") else 400
    return jsonify(res), status_code

@app.route("/api/encounters/active", methods=["GET"])
def get_active_admissions():
    """Lists all currently admitted patients across hospital wards."""
    admissions = crud_service.get_active_admissions()
    return jsonify({"success": True, "count": len(admissions), "data": parse_json(admissions)})

@app.route("/api/encounters/past", methods=["GET"])
def get_past_encounters():
    encounters = crud_service.get_discharged_encounters()
    return jsonify({"success": True, "count": len(encounters), "data": parse_json(encounters)})

@app.route("/api/appointments/upcoming", methods=["GET"])
def get_upcoming_appointments():
    appointments = crud_service.list_upcoming_appointments()
    return jsonify({"success": True, "data": parse_json(appointments)})

@app.route("/api/appointments/next-id", methods=["GET"])
def get_next_appointment_id():
    return jsonify({"success": True, "next_id": crud_service.get_next_appointment_id()})

@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    result = crud_service.create_appointment(request.get_json(silent=True) or {})
    return jsonify(result), 201 if result.get("success") else 400

@app.route("/api/appointments/<appointment_id>/cancel", methods=["POST"])
def cancel_scheduled_appointment(appointment_id):
    result = crud_service.cancel_scheduled_appointment(appointment_id)
    if result.get("matched_count", 0) == 0:
        return jsonify({"success": False, "error": "Scheduled appointment was not found."}), 404
    return jsonify({"success": True, "message": f"Appointment {appointment_id} cancelled."})

@app.route("/api/encounters/<encounter_id>/vitals", methods=["POST"])
def record_vital_reading(encounter_id):
    """Nurse Station: Bedside vitals telemetry logging."""
    reading = request.json or {}
    res = crud_service.append_vital_reading(encounter_id, reading)
    if res.get("success") is False:
        return jsonify(res), 400
    if res.get("matched_count", 0) == 0:
        return jsonify({"success": False, "error": "No active encounter was found for this action."}), 404
    return jsonify({"success": True, "result": res, "message": "Bedside vitals logged successfully."})

@app.route("/api/encounters/<encounter_id>/prescriptions", methods=["POST"])
def add_prescription(encounter_id):
    """Doctor Station: Issue clinical prescription."""
    prescription = request.json or {}
    res = crud_service.add_prescription_to_encounter(encounter_id, prescription)
    if res.get("success") is False:
        return jsonify(res), 400
    if res.get("matched_count", 0) == 0:
        return jsonify({"success": False, "error": "No active encounter was found for this action."}), 404
    return jsonify({"success": True, "result": res})

@app.route("/api/encounters/<encounter_id>/notes", methods=["POST"])
def add_clinical_note(encounter_id):
    data = request.get_json(silent=True) or {}
    result = crud_service.add_clinical_note(encounter_id, data.get("note", ""), session.get("admin_username", "clinician"))
    return jsonify(result), 200 if result.get("success") else 400

@app.route("/api/encounters/<encounter_id>/discharge", methods=["POST"])
def discharge_patient(encounter_id):
    """Billing & Discharge: Discharges patient and updates itemized bill."""
    data = request.get_json(silent=True) or {}
    try:
        pharmacy_cost = float(data.get("pharmacy_cost", 0.0))
        if not math.isfinite(pharmacy_cost) or pharmacy_cost < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Pharmacy cost must be a non-negative number."}), 400
    res = crud_service.discharge_encounter(encounter_id, pharmacy_cost)
    if res.get("matched_count", 0) == 0:
        return jsonify({"success": False, "error": f"Encounter {encounter_id} was not found or is already discharged."}), 404
    return jsonify({"success": True, "result": res, "message": f"Encounter {encounter_id} discharged and bill finalized."})

@app.route("/api/doctors", methods=["GET"])
def list_doctors():
    department = request.args.get("department")
    doctors = crud_service.list_all_doctors(department)
    return jsonify({"success": True, "data": parse_json(doctors)})

@app.route("/api/encounters/abnormal-vitals", methods=["GET"])
def get_abnormal_encounters():
    min_hr = request.args.get("min_hr", default=100, type=int)
    encounters = crud_service.find_encounters_with_abnormal_vitals(min_hr)
    return jsonify({"success": True, "data": parse_json(encounters)})

# ==========================================
# API: SCHEMA VALIDATION SANDBOX
# ==========================================
@app.route("/api/sandbox/validate", methods=["POST"])
def test_validation():
    """
    Attempts to insert a document to test MongoDB $jsonSchema enforcement.
    Does not commit invalid data; rolls back or removes upon test.
    """
    payload = request.json
    coll_type = payload.get("type", "patient")
    doc = payload.get("document", {})
    db = get_database()

    try:
        if coll_type == "patient":
            if "dob" in doc and isinstance(doc["dob"], str):
                try:
                    doc["dob"] = datetime.strptime(doc["dob"], "%Y-%m-%d")
                except Exception:
                    pass
            # If doc has test id, cleanup first
            test_id = doc.get("patient_id", "PAT-TEST")
            db.patients.delete_one({"patient_id": test_id})
            res = db.patients.insert_one(doc)
            # Remove right after test
            db.patients.delete_one({"_id": res.inserted_id})
            return jsonify({
                "valid": True,
                "message": "PASSED: Document satisfies MongoDB $jsonSchema constraints!",
                "inserted_id": str(res.inserted_id)
            })
        elif coll_type == "doctor":
            test_id = doc.get("doctor_id", "DOC-TEST")
            db.doctors.delete_one({"doctor_id": test_id})
            res = db.doctors.insert_one(doc)
            db.doctors.delete_one({"_id": res.inserted_id})
            return jsonify({
                "valid": True,
                "message": "PASSED: Doctor document satisfies MongoDB $jsonSchema constraints!",
                "inserted_id": str(res.inserted_id)
            })
        else:
            return jsonify({"valid": False, "error": f"Unknown type: {coll_type}"}), 400
    except Exception as e:
        from pymongo.errors import WriteError
        from database.validators import parse_validation_error
        if isinstance(e, WriteError):
            friendly = parse_validation_error(e.details)
        else:
            friendly = str(e)
        return jsonify({
            "valid": False,
            "error_type": type(e).__name__,
            "error": friendly,
            "message": "REJECTED BY MONGODB ENGINE: Schema Validation Failed ($jsonSchema constraint violated)."
        }), 200

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    print(f"🚀 MediPulse Server running at http://{host}:{port}/ (Debug={debug})")
    app.run(host=host, port=port, debug=debug)
