"""
Automated Test Suite for MediPulse EHR & NoSQL System
CSE494: Intelligent NoSQL Databases - Academic Task 2
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from datetime import datetime, timedelta
from pymongo.errors import WriteError
from database.connection import get_database
from database.seed_data import seed_database
from services.crud_service import CRUDService
from services.aggregation_service import AggregationService

class TestMediPulseSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset and seed database for testing
        seed_database(reset=True)
        cls.db = get_database()
        cls.crud = CRUDService()
        cls.agg = AggregationService()

    @classmethod
    def tearDownClass(cls):
        from database.connection import close_connection
        close_connection()

    def test_admin_registration_and_password_reset(self):
        from app import app
        from unittest.mock import patch
        from urllib.parse import parse_qs, urlparse
        import uuid

        suffix = uuid.uuid4().hex
        initial_id = "primary"
        created_initial_account = self.db.admins.count_documents({}) == 0
        client = app.test_client()
        password = "Initial-Password-42!"
        if created_initial_account:
            setup = client.post("/api/auth/setup", json={
                "username": f"initial-{suffix[:10]}",
                "email": f"initial-{suffix}@example.com",
                "password": password,
                "password_confirm": password
            })
            self.assertEqual(setup.status_code, 200, setup.get_json())

        username = f"staff-{suffix[:12]}"
        email = f"staff-{suffix}@example.com"
        with patch("app.os.getenv", return_value=None):
            registered = client.post("/api/auth/register", json={
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password
            })
        self.assertEqual(registered.status_code, 200, registered.get_json())

        mail_environment = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_FROM": "noreply@example.com",
            "PUBLIC_BASE_URL": "https://medipulse.example.com"
        }
        try:
            with patch("app.os.getenv", side_effect=lambda key, default=None: mail_environment.get(key, default)):
                with patch("app.send_password_reset_email") as send_reset:
                    requested = client.post("/api/auth/password-reset", json={"email": email})
            self.assertEqual(requested.status_code, 200, requested.get_json())
            reset_url = send_reset.call_args.args[1]
            token = parse_qs(urlparse(reset_url).query)["token"][0]
            new_password = "Updated-Password-73!"
            reset = client.post("/api/auth/password-reset/complete", json={
                "token": token,
                "password": new_password,
                "password_confirm": new_password
            })
            self.assertEqual(reset.status_code, 200, reset.get_json())
            reused = client.post("/api/auth/password-reset/complete", json={
                "token": token,
                "password": password,
                "password_confirm": password
            })
            self.assertEqual(reused.status_code, 400)
            client.post("/api/auth/logout")
            signed_in = client.post("/api/auth/login", json={"username": username, "password": new_password})
            self.assertEqual(signed_in.status_code, 200, signed_in.get_json())

            previous_debug = app.config["DEBUG"]
            app.config["DEBUG"] = True
            try:
                with patch("app.os.getenv", return_value=None):
                    local_requested = client.post("/api/auth/password-reset", json={"email": email})
            finally:
                app.config["DEBUG"] = previous_debug
            self.assertEqual(local_requested.status_code, 200, local_requested.get_json())
            self.assertIn("dev_reset_url", local_requested.get_json())
            local_token = parse_qs(urlparse(local_requested.get_json()["dev_reset_url"]).query)["token"][0]
            local_password = "Local-Password-81!"
            local_reset = client.post("/api/auth/password-reset/complete", json={
                "token": local_token,
                "password": local_password,
                "password_confirm": local_password
            })
            self.assertEqual(local_reset.status_code, 200, local_reset.get_json())
            client.post("/api/auth/logout")
            local_sign_in = client.post("/api/auth/login", json={"username": username, "password": local_password})
            self.assertEqual(local_sign_in.status_code, 200, local_sign_in.get_json())
        finally:
            self.db.admins.delete_one({"_id": username.casefold()})
            if created_initial_account:
                self.db.admins.delete_one({"_id": initial_id})

    # ---------------------------------------------
    # 1. Schema Validation Tests
    # ---------------------------------------------
    def test_schema_valid_patient_insert(self):
        """Tests that a valid patient document satisfies $jsonSchema."""
        doc = {
            "patient_id": "PAT-7777",
            "name": "Karan Malhotra",
            "dob": datetime(1991, 7, 10),
            "gender": "Male",
            "blood_group": "AB+",
            "contact": {
                "phone": "+91-9876543299",
                "email": "karan.m@example.com"
            },
            "status": "Active"
        }
        res = self.crud.add_patient(doc)
        self.assertTrue(res.get("success"), f"Failed to insert valid patient: {res.get('error')}")
        # Clean up
        self.db.patients.delete_one({"patient_id": "PAT-7777"})

    def test_schema_invalid_blood_group_rejected(self):
        """Tests that MongoDB engine rejects an invalid blood group."""
        doc = {
            "patient_id": "PAT-7778",
            "name": "Invalid BG Patient",
            "dob": datetime(1991, 7, 10),
            "gender": "Male",
            "blood_group": "X+",  # Invalid enum!
            "contact": {
                "phone": "+91-9876543299",
                "email": "invalid@example.com"
            }
        }
        res = self.crud.add_patient(doc)
        self.assertFalse(res.get("success"))
        self.assertIn("Schema Validation Failed", res.get("error"))

    def test_schema_invalid_phone_format_rejected(self):
        """Tests that phone numbers not matching the regex pattern are rejected."""
        doc = {
            "patient_id": "PAT-7779",
            "name": "Invalid Phone Patient",
            "dob": datetime(1991, 7, 10),
            "gender": "Male",
            "blood_group": "O+",
            "contact": {
                "phone": "abc-123",  # Invalid regex!
                "email": "invalidphone@example.com"
            }
        }
        res = self.crud.add_patient(doc)
        self.assertFalse(res.get("success"))

    # ---------------------------------------------
    # 2. CRUD Operations Tests
    # ---------------------------------------------
    def test_read_patient_by_id(self):
        patient = self.crud.get_patient_by_id("PAT-1001")
        self.assertIsNotNone(patient)
        self.assertEqual(patient.get("name"), "Arjun Sharma")
        self.assertEqual(patient.get("blood_group"), "B+")

    def test_update_and_delete_unreferenced_patient(self):
        patient = {
            "patient_id": "PAT-7790",
            "name": "Test Patient",
            "dob": datetime(1990, 1, 1),
            "gender": "Female",
            "blood_group": "O+",
            "contact": {"phone": "+91-9876543200", "email": "test.patient@example.com"}
        }
        self.assertTrue(self.crud.add_patient(patient).get("success"))
        updated = self.crud.update_patient("PAT-7790", {
            "name": "Updated Patient",
            "dob": "1991-02-03",
            "gender": "Female",
            "blood_group": "A+",
            "phone": "+91-9876543201",
            "email": "updated.patient@example.com",
            "chronic_conditions": ["Asthma"]
        })
        self.assertTrue(updated.get("success"), updated.get("error"))
        saved = self.crud.get_patient_by_id("PAT-7790")
        self.assertEqual(saved["name"], "Updated Patient")
        self.assertEqual(saved["contact"]["phone"], "+91-9876543201")
        self.assertEqual(saved["medical_profile"]["chronic_conditions"], ["Asthma"])

        deleted = self.crud.delete_patient("PAT-7790")
        self.assertEqual(deleted.get("deleted_count"), 1)
        self.assertIsNone(self.crud.get_patient_by_id("PAT-7790"))

        protected = self.crud.delete_patient("PAT-1001")
        self.assertFalse(protected.get("success"))
        self.assertIn("clinical encounters or appointments", protected.get("error", ""))

    def test_create_encounter_validates_patient_and_doctor(self):
        missing_patient = self.crud.add_encounter({
            "patient_id": "PAT-9999",
            "doctor_id": "DOC-001",
            "type": "Inpatient",
            "status": "Admitted"
        })
        self.assertFalse(missing_patient.get("success"))
        self.assertIn("Patient PAT-9999 was not found", missing_patient.get("error", ""))

        doctor = self.db.doctors.find_one({"active": True})
        created = self.crud.add_encounter({
            "patient_id": "PAT-1001",
            "doctor_id": doctor["doctor_id"],
            "type": "Inpatient",
            "status": "Admitted",
            "primary_diagnosis": "CRUD integration test"
        })
        self.assertTrue(created.get("success"), created.get("error"))
        self.db.encounters.delete_one({"encounter_id": created["encounter_id"]})

    def test_read_patients_by_blood_group(self):
        patients = self.crud.search_patients_by_blood_group("B+")
        self.assertGreaterEqual(len(patients), 1)
        self.assertEqual(patients[0]["blood_group"], "B+")

    def test_text_search(self):
        results = self.crud.text_search_patients("Asthma")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["patient_id"], "PAT-1002")

    def test_elemmatch_abnormal_vitals(self):
        encounters = self.crud.find_encounters_with_abnormal_vitals(100)
        self.assertGreaterEqual(len(encounters), 1)
        # Check that the returned vital reading had heart_rate >= 100
        first_vital = encounters[0]["vitals_log"][0]
        self.assertGreaterEqual(first_vital["heart_rate"], 100)

    def test_update_push_vital(self):
        new_vital = {
            "timestamp": datetime.now(),
            "heart_rate": 80,
            "spo2": 98,
            "temperature_f": 98.6
        }
        res = self.crud.append_vital_reading("ENC-5006", new_vital)
        self.assertEqual(res["modified_count"], 1)

    def test_clinical_chart_actions_and_followup_appointment(self):
        encounter_id = "ENC-7797"
        self.db.encounters.insert_one({
            "encounter_id": encounter_id,
            "patient_id": "PAT-1001",
            "doctor_id": "DOC-201",
            "department": "Cardiology",
            "type": "Outpatient",
            "status": "Admitted",
            "primary_diagnosis": "Chart action integration test",
            "admission_date": datetime.now(),
            "vitals_log": [],
            "prescriptions": [],
            "billing": {"total_amount": 0.0, "payment_status": "Pending"}
        })
        appointment_id = None
        try:
            note_result = self.crud.add_clinical_note(encounter_id, "Symptoms improving", "test-clinician")
            vital_result = self.crud.append_vital_reading(encounter_id, {"heart_rate": 72, "spo2": 98})
            prescription_result = self.crud.add_prescription_to_encounter(encounter_id, {
                "medication": "Test medicine", "dosage": "10 mg", "frequency": "Once daily", "duration_days": 7
            })
            self.assertTrue(note_result["success"])
            self.assertEqual(vital_result["modified_count"], 1)
            self.assertEqual(prescription_result["modified_count"], 1)
            saved_encounter = self.db.encounters.find_one({"encounter_id": encounter_id})
            self.assertEqual(saved_encounter["clinical_notes"][0]["note"], "Symptoms improving")
            self.assertEqual(saved_encounter["vitals_log"][0]["heart_rate"], 72)
            self.assertEqual(saved_encounter["prescriptions"][0]["medication"], "Test medicine")

            appointment_result = self.crud.create_appointment({
                "patient_id": "PAT-1001",
                "doctor_id": "DOC-201",
                "appointment_time": (datetime.now() + timedelta(days=3)).isoformat(timespec="minutes"),
                "reason": "Post-visit follow-up"
            })
            self.assertTrue(appointment_result["success"], appointment_result.get("error"))
            appointment_id = appointment_result["appointment_id"]
            cancel_result = self.crud.cancel_scheduled_appointment(appointment_id)
            self.assertEqual(cancel_result["modified_count"], 1)
            self.assertEqual(self.db.appointments.find_one({"appointment_id": appointment_id})["status"], "Cancelled")
        finally:
            self.db.encounters.delete_one({"encounter_id": encounter_id})
            if appointment_id:
                self.db.appointments.delete_one({"appointment_id": appointment_id})

    def test_update_atomic_discharge(self):
        res = self.crud.discharge_encounter("ENC-5008", pharmacy_cost=500.0)
        self.assertEqual(res["modified_count"], 1)
        enc = self.db.encounters.find_one({"encounter_id": "ENC-5008"})
        self.assertEqual(enc["status"], "Discharged")
        self.assertIsNotNone(enc["discharge_date"])

    def test_discharge_api_persists_bill_update(self):
        from app import app

        encounter_id = "ENC-7799"
        self.db.encounters.insert_one({
            "encounter_id": encounter_id,
            "patient_id": "PAT-1001",
            "doctor_id": "DOC-206",
            "department": "Oncology",
            "type": "Inpatient",
            "status": "Admitted",
            "primary_diagnosis": "Discharge API test",
            "admission_date": datetime.now(),
            "vitals_log": [],
            "prescriptions": [],
            "billing": {"pharmacy_charges": 0.0, "total_amount": 1000.0, "payment_status": "Pending", "insurance_claimed": 0.0}
        })
        client = app.test_client()
        with client.session_transaction() as session:
            session["admin_username"] = "test-admin"

        try:
            response = client.post(f"/api/encounters/{encounter_id}/discharge", json={"pharmacy_cost": 123.0})
            saved = self.db.encounters.find_one({"encounter_id": encounter_id})
            self.assertEqual(response.status_code, 200, response.get_json())
            self.assertEqual(saved["status"], "Discharged")
            self.assertEqual(saved["billing"]["pharmacy_charges"], 123.0)
            self.assertEqual(saved["billing"]["total_amount"], 1123.0)
            archived = self.crud.get_discharged_encounters()
            self.assertIn(encounter_id, [encounter["encounter_id"] for encounter in archived])
            repeated = client.post(f"/api/encounters/{encounter_id}/discharge", json={"pharmacy_cost": 10.0})
            self.assertEqual(repeated.status_code, 404)
        finally:
            self.db.encounters.delete_one({"encounter_id": encounter_id})

    # ---------------------------------------------
    # 3. Aggregation Pipelines Tests
    # ---------------------------------------------
    def test_pipeline_1_department_financials(self):
        res = self.agg.get_department_financial_analytics()
        self.assertIsInstance(res, list)
        self.assertGreater(len(res), 0)
        # Verify required keys in output
        self.assertIn("department", res[0])
        self.assertIn("total_revenue", res[0])
        self.assertIn("total_encounters", res[0])

    def test_pipeline_2_doctor_lookup_workload(self):
        res = self.agg.get_doctor_performance_analytics()
        self.assertIsInstance(res, list)
        self.assertGreater(len(res), 0)
        self.assertIn("doctor_name", res[0])
        self.assertIn("total_billing_generated", res[0])

    def test_pipeline_3_medication_utilization(self):
        res = self.agg.get_medication_utilization_analytics(3)
        self.assertIsInstance(res, list)
        self.assertLessEqual(len(res), 3)
        self.assertIn("medication", res[0])
        self.assertIn("prescription_count", res[0])

    def test_pipeline_4_executive_facet(self):
        res = self.agg.get_executive_kpi_dashboard()
        self.assertIn("encounter_type_distribution", res)
        self.assertIn("status_overview", res)
        self.assertIn("financial_overview", res)
        self.assertIn("critical_vitals_count", res)

    def test_pipeline_5_age_stratification(self):
        res = self.agg.get_patient_age_stratification()
        self.assertIsInstance(res, list)
        self.assertGreater(len(res), 0)
        self.assertIn("age_bracket", res[0])
        self.assertIn("patient_count", res[0])

if __name__ == "__main__":
    unittest.main()
