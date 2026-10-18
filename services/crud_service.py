"""
CRUD Operations Service Layer for MediPulse EHR
CSE494: Intelligent NoSQL Databases - Academic Task 2

Implements standard and advanced CRUD operations using PyMongo:
- Create: insert_one, insert_many
- Read: find, find_one, projection, filtering ($and, $or, $gt, $in, $elemMatch, text search)
- Update: update_one, update_many ($set, $push, $inc, $pull, $addToSet)
- Delete: delete_one, delete_many
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo.errors import WriteError, DuplicateKeyError
from database.connection import get_database
from database.validators import parse_validation_error
import logging
import re

logger = logging.getLogger("MediPulseCRUD")

class CRUDService:
    def __init__(self):
        self.db = get_database()
        self.patients = self.db.patients
        self.doctors = self.db.doctors
        self.encounters = self.db.encounters
        self.appointments = self.db.appointments

    def get_next_patient_id(self) -> str:
        """
        Calculates the next available sequential Patient ID (e.g., PAT-1009).
        """
        cursor = self.patients.find({}, {"patient_id": 1, "_id": 0})
        max_num = 1000
        for doc in cursor:
            pid = doc.get("patient_id", "")
            match = re.search(r"PAT-(\d+)", pid)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        return f"PAT-{max_num + 1}"

    # ==========================================
    # 1. CREATE OPERATIONS (insert_one, insert_many)
    # ==========================================
    def add_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new patient document.
        Normalizes inputs (ID formatting, DOB parsing) and validates via $jsonSchema.
        """
        try:
            # 1. Normalize Patient ID
            pid = str(patient_data.get("patient_id", "")).strip()
            if not pid:
                pid = self.get_next_patient_id()
                patient_data["patient_id"] = pid
            elif not pid.startswith("PAT-"):
                if pid.isdigit():
                    patient_data["patient_id"] = f"PAT-{int(pid):04d}"
                else:
                    patient_data["patient_id"] = f"PAT-{pid}"

            # 2. Parse Date of Birth if string
            if "dob" in patient_data and isinstance(patient_data["dob"], str):
                dob_str = patient_data["dob"].strip()
                parsed_dob = None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                    try:
                        parsed_dob = datetime.strptime(dob_str, fmt)
                        break
                    except ValueError:
                        continue
                if parsed_dob:
                    patient_data["dob"] = parsed_dob
                else:
                    try:
                        patient_data["dob"] = datetime.fromisoformat(dob_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

            # 3. Ensure required structure defaults
            if "registered_at" not in patient_data:
                patient_data["registered_at"] = datetime.now()
            if "status" not in patient_data:
                patient_data["status"] = "Active"

            result = self.patients.insert_one(patient_data)
            return {
                "success": True,
                "inserted_id": str(result.inserted_id),
                "patient_id": patient_data.get("patient_id"),
                "message": f"Patient {patient_data.get('patient_id')} registered successfully."
            }
        except DuplicateKeyError:
            next_id = self.get_next_patient_id()
            return {
                "success": False,
                "error": f"Duplicate ID: Patient ID '{patient_data.get('patient_id')}' already exists in the database. Suggested next ID: {next_id}"
            }
        except WriteError as e:
            friendly_err = parse_validation_error(e.details)
            return {
                "success": False,
                "error": f"Schema Validation Failed: {friendly_err}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_next_encounter_id(self) -> str:
        """Calculates next sequential Encounter ID (e.g. ENC-5009)."""
        cursor = self.encounters.find({}, {"encounter_id": 1, "_id": 0})
        max_num = 5000
        for doc in cursor:
            eid = doc.get("encounter_id", "")
            match = re.search(r"ENC-(\d+)", eid)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        return f"ENC-{max_num + 1}"

    def add_encounter(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a clinical encounter (Inpatient, Outpatient, or Emergency).
        Demonstrates embedded documents (vitals_log, prescriptions, billing).
        """
        try:
            patient_id = encounter_data.get("patient_id")
            doctor_id = encounter_data.get("doctor_id")
            if not self.patients.find_one({"patient_id": patient_id}, {"_id": 1}):
                return {"success": False, "error": f"Patient {patient_id} was not found."}
            doctor = self.doctors.find_one({"doctor_id": doctor_id, "active": True}, {"department": 1})
            if not doctor:
                return {"success": False, "error": f"Active doctor {doctor_id} was not found."}
            encounter_data.setdefault("department", doctor.get("department", "General Medicine"))
            encounter_data.setdefault("status", "Admitted")
            if not encounter_data.get("encounter_id"):
                encounter_data["encounter_id"] = self.get_next_encounter_id()
            if "admission_date" not in encounter_data:
                encounter_data["admission_date"] = datetime.now()
            elif isinstance(encounter_data["admission_date"], str):
                try:
                    encounter_data["admission_date"] = datetime.strptime(encounter_data["admission_date"], "%Y-%m-%d")
                except Exception:
                    encounter_data["admission_date"] = datetime.now()
            
            if "vitals_log" not in encounter_data:
                encounter_data["vitals_log"] = []
            if "prescriptions" not in encounter_data:
                encounter_data["prescriptions"] = []
            if "billing" not in encounter_data:
                encounter_data["billing"] = {
                    "room_charges": 0.0,
                    "consultation_charges": 1000.0,
                    "pharmacy_charges": 0.0,
                    "lab_charges": 0.0,
                    "total_amount": 1000.0,
                    "payment_status": "Pending",
                    "insurance_claimed": 0.0
                }

            result = self.encounters.insert_one(encounter_data)
            return {
                "success": True,
                "inserted_id": str(result.inserted_id),
                "encounter_id": encounter_data.get("encounter_id"),
                "message": f"Clinical admission {encounter_data.get('encounter_id')} created successfully."
            }
        except WriteError as e:
            friendly = parse_validation_error(e.details)
            return {"success": False, "error": f"Schema Validation Failed: {friendly}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_prescription_to_encounter(self, encounter_id: str, prescription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demonstrates $push operator: Doctor issues a new prescription to an encounter.
        """
        required_fields = ("medication", "dosage", "frequency", "duration_days")
        if any(not prescription.get(field) for field in required_fields):
            return {"matched_count": 0, "success": False, "error": "Medication, dosage, frequency, and duration are required."}
        if "status" not in prescription:
            prescription["status"] = "Active"
        result = self.encounters.update_one(
            {"encounter_id": encounter_id, "status": {"$in": ["Admitted", "Under_Observation"]}},
            {"$push": {"prescriptions": prescription}}
        )
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "message": f"Prescription for {prescription.get('medication')} added to {encounter_id}."
        }

    def get_active_admissions(self) -> List[Dict[str, Any]]:
        """
        Retrieves all currently admitted patients across hospital wards
        with attending doctor details and latest telemetry vitals.
        """
        pipeline = [
            {"$match": {"status": {"$in": ["Admitted", "Under_Observation"]}}},
            {
                "$lookup": {
                    "from": "patients",
                    "localField": "patient_id",
                    "foreignField": "patient_id",
                    "as": "patient_info"
                }
            },
            {"$unwind": {"path": "$patient_info", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "doctors",
                    "localField": "doctor_id",
                    "foreignField": "doctor_id",
                    "as": "doctor_info"
                }
            },
            {"$unwind": {"path": "$doctor_info", "preserveNullAndEmptyArrays": True}},
            {"$sort": {"admission_date": -1}}
        ]
        results = list(self.encounters.aggregate(pipeline))
        for enc in results:
            enc["_id"] = str(enc.get("_id", ""))
            v_log = enc.get("vitals_log", [])
            enc["latest_vital"] = v_log[-1] if v_log else None
        return results

    def get_discharged_encounters(self, limit: int = 100) -> List[Dict[str, Any]]:
        encounters = list(self.encounters.find(
            {"status": "Discharged"},
            {"_id": 0}
        ).sort("discharge_date", -1).limit(limit))
        for encounter in encounters:
            patient = self.patients.find_one({"patient_id": encounter.get("patient_id")}, {"_id": 0, "name": 1})
            doctor = self.doctors.find_one({"doctor_id": encounter.get("doctor_id")}, {"_id": 0, "name": 1})
            encounter["patient_name"] = patient.get("name", "Unknown patient") if patient else "Unknown patient"
            encounter["doctor_name"] = doctor.get("name", "Unknown clinician") if doctor else "Unknown clinician"
        return encounters

    def bulk_add_appointments(self, appointments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk insertion of multiple appointment documents using insert_many.
        """
        try:
            result = self.appointments.insert_many(appointments, ordered=True)
            return {
                "success": True,
                "inserted_count": len(result.inserted_ids),
                "inserted_ids": [str(i) for i in result.inserted_ids]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # 2. READ OPERATIONS (find_one, find, filters, text search, $elemMatch)
    # ==========================================
    def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single patient by unique patient_id using projection to exclude internal _id.
        """
        return self.patients.find_one({"patient_id": patient_id}, {"_id": 0})

    def search_patients_by_blood_group(self, blood_group: str) -> List[Dict[str, Any]]:
        """
        Query with equality filter and projection.
        """
        cursor = self.patients.find(
            {"blood_group": blood_group},
            {"_id": 0, "patient_id": 1, "name": 1, "gender": 1, "blood_group": 1, "contact.phone": 1}
        )
        return list(cursor)

    def search_patients_compound_filter(self, city: Optional[str] = None, has_condition: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Demonstrates compound filtering with $and, $or, and array containment.
        """
        query_clauses = [{"status": "Active"}]
        if city:
            query_clauses.append({"contact.address.city": city})
        if has_condition:
            query_clauses.append({"medical_profile.chronic_conditions": has_condition})

        query = {"$and": query_clauses} if len(query_clauses) > 1 else query_clauses[0]
        return list(self.patients.find(query, {"_id": 0}))

    def text_search_patients(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Demonstrates Full-Text Search on indexed fields (name, chronic_conditions).
        """
        cursor = self.patients.find(
            {"$text": {"$search": search_term}},
            {"_id": 0, "patient_id": 1, "name": 1, "medical_profile": 1, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])
        return list(cursor)

    def find_encounters_with_abnormal_vitals(self, min_heart_rate: int = 100) -> List[Dict[str, Any]]:
        """
        Demonstrates $elemMatch to query within nested arrays of documents.
        Finds encounters where any logged vital reading has heart rate >= threshold.
        """
        query = {
            "vitals_log": {
                "$elemMatch": {
                    "heart_rate": {"$gte": min_heart_rate}
                }
            }
        }
        projection = {
            "_id": 0,
            "encounter_id": 1,
            "patient_id": 1,
            "department": 1,
            "primary_diagnosis": 1,
            "vitals_log.$": 1  # Projects only the matching element of the array!
        }
        return list(self.encounters.find(query, projection))

    def list_all_doctors(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists doctors, optionally filtered by department.
        """
        filter_q = {"active": True}
        if department:
            filter_q["department"] = department
        return list(self.doctors.find(filter_q, {"_id": 0}).sort("experience_years", -1))

    def get_patient_ehr_summary(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieves a complete Electronic Health Record:
        Patient demographics + all clinical encounters + scheduled appointments.
        """
        patient = self.patients.find_one({"patient_id": patient_id}, {"_id": 0})
        if not patient:
            return {"found": False, "error": f"Patient {patient_id} not found"}

        encounters = list(self.encounters.find({"patient_id": patient_id}, {"_id": 0}).sort("admission_date", -1))
        appointments = list(self.appointments.find({"patient_id": patient_id}, {"_id": 0}).sort("appointment_time", 1))

        return {
            "found": True,
            "patient": patient,
            "encounters": encounters,
            "appointments": appointments,
            "total_encounters": len(encounters),
            "upcoming_appointments": len(appointments)
        }

    def add_clinical_note(self, encounter_id: str, note: str, author: str) -> Dict[str, Any]:
        note_text = str(note).strip()
        if not note_text:
            return {"success": False, "error": "Clinical note cannot be empty."}
        result = self.encounters.update_one(
            {"encounter_id": encounter_id, "status": {"$in": ["Admitted", "Under_Observation"]}},
            {"$push": {"clinical_notes": {"note": note_text, "author": author, "created_at": datetime.now()}}}
        )
        if result.matched_count == 0:
            return {"success": False, "error": "No active encounter was found for this action."}
        return {"success": True, "modified_count": result.modified_count}

    def get_next_appointment_id(self) -> str:
        max_number = 9000
        for document in self.appointments.find({}, {"appointment_id": 1, "_id": 0}):
            match = re.search(r"APT-(\d+)", document.get("appointment_id", ""))
            if match:
                max_number = max(max_number, int(match.group(1)))
        return f"APT-{max_number + 1}"

    def list_upcoming_appointments(self, limit: int = 12) -> List[Dict[str, Any]]:
        appointments = list(self.appointments.find(
            {"status": "Scheduled", "appointment_time": {"$gte": datetime.now()}},
            {"_id": 0}
        ).sort("appointment_time", 1).limit(limit))
        for appointment in appointments:
            patient = self.patients.find_one({"patient_id": appointment["patient_id"]}, {"_id": 0, "name": 1})
            doctor = self.doctors.find_one({"doctor_id": appointment["doctor_id"]}, {"_id": 0, "name": 1, "department": 1})
            appointment["patient_name"] = patient.get("name", "Unknown patient") if patient else "Unknown patient"
            appointment["doctor_name"] = doctor.get("name", "Unknown clinician") if doctor else "Unknown clinician"
            appointment["department"] = doctor.get("department", "") if doctor else ""
        return appointments

    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_id = str(appointment_data.get("patient_id", "")).strip()
        doctor_id = str(appointment_data.get("doctor_id", "")).strip()
        reason = str(appointment_data.get("reason", "")).strip()
        if not self.patients.find_one({"patient_id": patient_id}, {"_id": 1}):
            return {"success": False, "error": f"Patient {patient_id} was not found."}
        if not self.doctors.find_one({"doctor_id": doctor_id, "active": True}, {"_id": 1}):
            return {"success": False, "error": f"Active clinician {doctor_id} was not found."}
        if len(reason) < 3:
            return {"success": False, "error": "Enter a follow-up reason of at least 3 characters."}
        try:
            appointment_time = datetime.fromisoformat(str(appointment_data.get("appointment_time", "")))
            if appointment_time.tzinfo is not None:
                appointment_time = appointment_time.astimezone().replace(tzinfo=None)
        except (TypeError, ValueError):
            return {"success": False, "error": "Choose a valid appointment date and time."}
        if appointment_time <= datetime.now():
            return {"success": False, "error": "Follow-up time must be in the future."}

        appointment_id = self.get_next_appointment_id()
        try:
            self.appointments.insert_one({
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_time": appointment_time,
                "reason": reason,
                "status": "Scheduled"
            })
        except Exception as error:
            return {"success": False, "error": str(error)}
        return {"success": True, "appointment_id": appointment_id}

    def cancel_scheduled_appointment(self, appointment_id: str) -> Dict[str, Any]:
        result = self.appointments.update_one(
            {"appointment_id": appointment_id, "status": "Scheduled"},
            {"$set": {"status": "Cancelled", "cancelled_at": datetime.now()}}
        )
        return {"matched_count": result.matched_count, "modified_count": result.modified_count}

    # ==========================================
    # 3. UPDATE OPERATIONS ($set, $push, $inc, $pull, $addToSet)
    # ==========================================
    def update_patient_contact(self, patient_id: str, new_phone: str, new_email: str) -> Dict[str, Any]:
        """
        Demonstrates $set operator to update nested contact fields.
        """
        result = self.patients.update_one(
            {"patient_id": patient_id},
            {
                "$set": {
                    "contact.phone": new_phone,
                    "contact.email": new_email,
                    "last_updated": datetime.now()
                }
            }
        )
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "acknowledged": result.acknowledged
        }

    def update_patient(self, patient_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates editable patient demographics and contact details."""
        editable_fields = {
            "name": "name",
            "gender": "gender",
            "blood_group": "blood_group",
            "contact.phone": "phone",
            "contact.email": "email",
            "medical_profile.chronic_conditions": "chronic_conditions"
        }
        updates = {
            field: patient_data[key]
            for field, key in editable_fields.items()
            if key in patient_data
        }

        if "dob" in patient_data:
            try:
                updates["dob"] = datetime.strptime(patient_data["dob"], "%Y-%m-%d")
            except (TypeError, ValueError):
                return {"success": False, "error": "Date of birth must use YYYY-MM-DD format."}

        for field in ("name", "contact.phone", "contact.email"):
            if field in updates:
                updates[field] = str(updates[field]).strip()
        if "chronic_conditions" in patient_data:
            updates["medical_profile.chronic_conditions"] = patient_data["chronic_conditions"]

        if not updates:
            return {"success": False, "error": "No editable patient fields were provided."}

        updates["last_updated"] = datetime.now()
        try:
            result = self.patients.update_one({"patient_id": patient_id}, {"$set": updates})
            if result.matched_count == 0:
                return {"success": False, "error": f"Patient {patient_id} was not found."}
            return {
                "success": True,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "message": f"Patient {patient_id} updated successfully."
            }
        except WriteError as e:
            friendly = parse_validation_error(e.details)
            return {"success": False, "error": f"Schema Validation Failed: {friendly}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_patient(self, patient_id: str) -> Dict[str, Any]:
        """Deletes an unreferenced patient, preserving linked clinical history."""
        patient = self.patients.find_one({"patient_id": patient_id}, {"_id": 1})
        if not patient:
            return {"success": False, "error": f"Patient {patient_id} was not found."}

        encounter_count = self.encounters.count_documents({"patient_id": patient_id})
        appointment_count = self.appointments.count_documents({"patient_id": patient_id})
        if encounter_count or appointment_count:
            return {
                "success": False,
                "error": "Patient cannot be deleted while clinical encounters or appointments are linked.",
                "encounter_count": encounter_count,
                "appointment_count": appointment_count
            }

        result = self.patients.delete_one({"patient_id": patient_id})
        return {"success": result.deleted_count == 1, "deleted_count": result.deleted_count}

    def add_allergy_to_patient(self, patient_id: str, allergy: str) -> Dict[str, Any]:
        """
        Demonstrates $addToSet operator (ensures allergy is only added if not already present).
        """
        result = self.patients.update_one(
            {"patient_id": patient_id},
            {"$addToSet": {"medical_profile.allergies": allergy}}
        )
        return {"matched_count": result.matched_count, "modified_count": result.modified_count}

    def append_vital_reading(self, encounter_id: str, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demonstrates $push operator to append a new vital observation to vitals_log array.
        """
        if "timestamp" not in reading:
            reading["timestamp"] = datetime.now()
        try:
            result = self.encounters.update_one(
                {"encounter_id": encounter_id, "status": {"$in": ["Admitted", "Under_Observation"]}},
                {"$push": {"vitals_log": reading}}
            )
            return {"matched_count": result.matched_count, "modified_count": result.modified_count}
        except WriteError as e:
            friendly = parse_validation_error(e.details)
            return {"matched_count": 0, "success": False, "error": f"Vital reading rejected: {friendly}"}

    def discharge_encounter(self, encounter_id: str, pharmacy_cost: float = 0.0) -> Dict[str, Any]:
        """
        Demonstrates atomic multi-operator update ($set + $inc):
        Sets status to Discharged, sets discharge_date, and increments pharmacy & total billing.
        """
        update_doc = {
            "$set": {
                "status": "Discharged",
                "discharge_date": datetime.now()
            }
        }
        if pharmacy_cost > 0:
            update_doc["$inc"] = {
                "billing.pharmacy_charges": pharmacy_cost,
                "billing.total_amount": pharmacy_cost
            }

        result = self.encounters.update_one(
            {"encounter_id": encounter_id, "status": "Admitted"},
            update_doc
        )
        return {"matched_count": result.matched_count, "modified_count": result.modified_count}

    def discontinue_prescription(self, encounter_id: str, medication_name: str) -> Dict[str, Any]:
        """
        Demonstrates $pull operator to remove an element matching condition from an array.
        """
        result = self.encounters.update_one(
            {"encounter_id": encounter_id},
            {"$pull": {"prescriptions": {"medication": medication_name}}}
        )
        return {"matched_count": result.matched_count, "modified_count": result.modified_count}

    def update_doctor_consultation_fees_by_dept(self, department: str, percentage_increase: float) -> Dict[str, Any]:
        """
        Demonstrates update_many: Bulk fee adjustment across all doctors in a department.
        Uses $mul operator.
        """
        multiplier = 1.0 + (percentage_increase / 100.0)
        result = self.doctors.update_many(
            {"department": department},
            {"$mul": {"consultation_fee": multiplier}}
        )
        return {"matched_count": result.matched_count, "modified_count": result.modified_count}

    # ==========================================
    # 4. DELETE OPERATIONS (delete_one, delete_many)
    # ==========================================
    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Demonstrates delete_one: Cancels and removes a scheduled appointment.
        """
        result = self.appointments.delete_one({"appointment_id": appointment_id})
        return {"deleted_count": result.deleted_count}

    def delete_cancelled_appointments(self) -> Dict[str, Any]:
        """
        Demonstrates delete_many: Purges all cancelled appointments.
        """
        result = self.appointments.delete_many({"status": "Cancelled"})
        return {"deleted_count": result.deleted_count}
