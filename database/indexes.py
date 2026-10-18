"""
MongoDB Index Management
CSE494: Intelligent NoSQL Databases - Academic Task 2

This module creates single-field, compound, unique, and text indexes
to optimize CRUD lookups and aggregation pipeline performance.
"""

from pymongo import ASCENDING, DESCENDING, TEXT

def create_indexes(db):
    """
    Creates necessary indexes across all MediPulse collections.
    """
    # 1. Patients Collection Indexes
    db.patients.create_index([("patient_id", ASCENDING)], unique=True, name="idx_patient_id_unique")
    db.patients.create_index([("blood_group", ASCENDING)], name="idx_blood_group")
    db.patients.create_index([("contact.address.city", ASCENDING), ("status", ASCENDING)], name="idx_city_status")
    db.patients.create_index([("name", TEXT), ("medical_profile.chronic_conditions", TEXT)], name="idx_patient_text_search")

    # 2. Doctors Collection Indexes
    db.doctors.create_index([("doctor_id", ASCENDING)], unique=True, name="idx_doctor_id_unique")
    db.doctors.create_index([("department", ASCENDING), ("active", ASCENDING)], name="idx_dept_active")
    db.doctors.create_index([("consultation_fee", ASCENDING)], name="idx_consultation_fee")

    # 3. Encounters Collection Indexes
    db.encounters.create_index([("encounter_id", ASCENDING)], unique=True, name="idx_encounter_id_unique")
    db.encounters.create_index([("patient_id", ASCENDING)], name="idx_encounter_patient")
    db.encounters.create_index([("doctor_id", ASCENDING)], name="idx_encounter_doctor")
    db.encounters.create_index([("department", ASCENDING), ("admission_date", DESCENDING)], name="idx_dept_admission")
    db.encounters.create_index([("status", ASCENDING)], name="idx_encounter_status")
    db.encounters.create_index([("primary_diagnosis", TEXT)], name="idx_diagnosis_text")
    db.encounters.create_index([("vitals_log.timestamp", DESCENDING)], name="idx_vitals_time")

    # 4. Appointments Collection Indexes
    db.appointments.create_index([("appointment_id", ASCENDING)], unique=True, name="idx_appointment_id_unique")
    db.appointments.create_index([("doctor_id", ASCENDING), ("appointment_time", ASCENDING)], name="idx_doc_time")
    db.appointments.create_index([("patient_id", ASCENDING)], name="idx_apt_patient")

    return True
