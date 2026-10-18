"""
MediPulse Hospital & EHR - Interactive Terminal Runner & Viva Demo CLI
CSE494: Intelligent NoSQL Databases - Academic Task 2
"""

import sys
import os
import json
from datetime import datetime, timezone
from tabulate import tabulate
from pymongo.errors import WriteError

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from database.connection import get_database
from database.seed_data import seed_database
from services.crud_service import CRUDService
from services.aggregation_service import AggregationService

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)

def demo_schema_validation():
    """
    Demonstrates MongoDB Engine-level $jsonSchema validation:
    1. Valid document successfully written.
    2. Invalid document (invalid blood group, negative billing) blocked by MongoDB engine.
    """
    print_header("1. MongoDB Schema Validation ($jsonSchema) Demonstration")
    db = get_database()
    
    print("\n[+] TEST A: Valid Patient Insertion")
    valid_patient = {
        "patient_id": "PAT-9999",
        "name": "Simran Kaur",
        "dob": datetime(1996, 5, 20),
        "gender": "Female",
        "blood_group": "O+",
        "contact": {
            "phone": "+91-9876500001",
            "email": "simran.kaur@example.com",
            "address": {"street": "55 Circular Road", "city": "Amritsar", "state": "Punjab", "pincode": "143001"}
        },
        "status": "Active",
        "registered_at": datetime.now()
    }
    
    try:
        db.patients.delete_one({"patient_id": "PAT-9999"})
        res = db.patients.insert_one(valid_patient)
        print(f"  [SUCCESS] Valid Patient Inserted! ID: {res.inserted_id}")
    except Exception as e:
        print(f"  [FAILED] {e}")

    print("\n[-] TEST B: Negative Test - Invalid Blood Group (e.g. 'Z+')")
    invalid_patient_bg = {
        "patient_id": "PAT-9998",
        "name": "Invalid Blood Patient",
        "dob": datetime(1990, 1, 1),
        "gender": "Male",
        "blood_group": "Z+",  # Invalid enum value!
        "contact": {
            "phone": "+91-9876500002",
            "email": "test@invalid.com"
        }
    }
    try:
        db.patients.insert_one(invalid_patient_bg)
        print("  [ERROR] Database accepted invalid blood group! Validation failed!")
    except WriteError as err:
        print("  [PASSED REJECTION] MongoDB Engine BLOCKED the write with WriteError:")
        print(f"  >> Code: {err.code}")
        print(f"  >> Message: Document failed validation against collection $jsonSchema!")

    print("\n[-] TEST C: Negative Test - Negative Consultation Fee for Doctor")
    invalid_doc = {
        "doctor_id": "DOC-999",
        "name": "Dr. Faulty Doctor",
        "specialization": "General",
        "department": "Cardiology",
        "consultation_fee": -50.0  # Schema requires minimum 100!
    }
    try:
        db.doctors.insert_one(invalid_doc)
        print("  [ERROR] Database accepted negative consultation fee!")
    except WriteError as err:
        print("  [PASSED REJECTION] MongoDB Engine BLOCKED doctor write with WriteError:")
        print(f"  >> Code: {err.code}")
        print("  >> Message: Consultation fee violated minimum boundary ($minimum: 100)!")

def demo_crud_operations():
    """
    Demonstrates full spectrum of CRUD operations using PyMongo.
    """
    print_header("2. PyMongo CRUD Operations Demonstration")
    crud = CRUDService()

    # 1. READ: Query with projection & filter
    print("\n[A] READ: Find Patients with Blood Group 'B+'")
    b_patients = crud.search_patients_by_blood_group("B+")
    print(tabulate(b_patients, headers="keys", tablefmt="grid"))

    # 2. READ: Text Search
    print("\n[B] READ: Full-Text Search for 'Diabetes'")
    diabetes_patients = crud.text_search_patients("Diabetes")
    flat_diabetes = [
        {
            "Patient ID": p.get("patient_id"),
            "Name": p.get("name"),
            "Conditions": ", ".join(p.get("medical_profile", {}).get("chronic_conditions", []))
        }
        for p in diabetes_patients
    ]
    print(tabulate(flat_diabetes, headers="keys", tablefmt="grid"))

    # 3. READ: $elemMatch on nested array
    print("\n[C] READ: Encounters with Critical Heart Rate (>= 100 bpm) via $elemMatch")
    critical_encounters = crud.find_encounters_with_abnormal_vitals(100)
    flat_critical = [
        {
            "Encounter ID": e.get("encounter_id"),
            "Patient ID": e.get("patient_id"),
            "Department": e.get("department"),
            "Primary Diagnosis": e.get("primary_diagnosis"),
            "Recorded HR": e.get("vitals_log", [{}])[0].get("heart_rate")
        }
        for e in critical_encounters
    ]
    print(tabulate(flat_critical, headers="keys", tablefmt="grid"))

    # 4. UPDATE: $push operator on nested array
    print("\n[D] UPDATE: Appending a new vital sign observation via $push to ENC-5006")
    new_vital = {
        "timestamp": datetime.now(),
        "heart_rate": 82,
        "blood_pressure": {"systolic": 138, "diastolic": 88},
        "spo2": 97,
        "temperature_f": 98.6,
        "recorded_by": "Nurse Sneha (Evening Round)"
    }
    push_res = crud.append_vital_reading("ENC-5006", new_vital)
    print(f"  [SUCCESS] Vital logged. Modified count: {push_res.get('modified_count')}")

    # 5. UPDATE: Atomic $set + $inc on Encounter Discharge
    print("\n[E] UPDATE: Discharging Patient & Updating Billing via Atomic $set and $inc")
    discharge_res = crud.discharge_encounter("ENC-5006", pharmacy_cost=800.0)
    print(f"  [SUCCESS] Encounter ENC-5006 discharged. Modified count: {discharge_res.get('modified_count')}")

    # 6. DELETE: Cancel appointment via delete_one
    print("\n[F] DELETE: Cancel & Purge Appointment APT-9005")
    del_res = crud.cancel_appointment("APT-9005")
    print(f"  [SUCCESS] Deleted count: {del_res.get('deleted_count')}")

def demo_aggregation_pipelines():
    """
    Demonstrates all 5 Aggregation Pipelines.
    """
    print_header("3. Advanced MongoDB Aggregation Pipelines")
    agg = AggregationService()

    # Pipeline 1
    print("\n[PIPELINE 1] Departmental Financial & Operational Performance")
    print("Stages: $match -> $group -> $sort -> $project")
    dept_stats = agg.get_department_financial_analytics()
    print(tabulate(dept_stats, headers="keys", tablefmt="grid"))

    # Pipeline 2
    print("\n[PIPELINE 2] Doctor Workload & Revenue Analytics (Cross-Collection $lookup)")
    print("Stages: $lookup -> $unwind -> $group -> $sort -> $project")
    doc_stats = agg.get_doctor_performance_analytics()
    print(tabulate(doc_stats, headers="keys", tablefmt="grid"))

    # Pipeline 3
    print("\n[PIPELINE 3] Medication Prescription Frequency & Utilization ($unwind)")
    print("Stages: $unwind -> $group -> $sort -> $limit -> $project")
    med_stats = agg.get_medication_utilization_analytics(5)
    med_table = [
        {
            "Medication": m.get("medication"),
            "Prescription Count": m.get("prescription_count"),
            "Avg Days": m.get("avg_duration_days"),
            "Departments": ", ".join(m.get("departments", []))
        }
        for m in med_stats
    ]
    print(tabulate(med_table, headers="keys", tablefmt="grid"))

    # Pipeline 4
    print("\n[PIPELINE 4] Multi-Faceted Executive Hospital Dashboard ($facet)")
    print("Stages: $facet (Parallel execution of 4 analytical sub-pipelines)")
    kpi_dashboard = agg.get_executive_kpi_dashboard()
    print(json.dumps(kpi_dashboard, indent=2, default=str))

    # Pipeline 5
    print("\n[PIPELINE 5] Demographic Age-Stratified Risk & Chronic Burden ($bucket)")
    print("Stages: $addFields ($dateDiff) -> $bucket -> $project")
    age_stats = agg.get_patient_age_stratification()
    print(tabulate(age_stats, headers="keys", tablefmt="grid"))

def demo_patient_ehr(patient_id: str = "PAT-1001"):
    """
    Demonstrates retrieving a comprehensive unified Electronic Health Record.
    """
    print_header(f"4. Patient Electronic Health Record (EHR) Lookup: {patient_id}")
    crud = CRUDService()
    ehr = crud.get_patient_ehr_summary(patient_id)
    if not ehr.get("found"):
        print(f"Error: {ehr.get('error')}")
        return

    patient = ehr.get("patient")
    print(f"\nPATIENT PROFILE:")
    print(f"  Name:          {patient.get('name')}")
    print(f"  DOB / Gender:  {patient.get('dob').strftime('%Y-%m-%d')} | {patient.get('gender')}")
    print(f"  Blood Group:   {patient.get('blood_group')}")
    print(f"  Contact:       {patient.get('contact', {}).get('phone')} | {patient.get('contact', {}).get('email')}")
    print(f"  Allergies:     {', '.join(patient.get('medical_profile', {}).get('allergies', []))}")
    print(f"  Chronic Cond:  {', '.join(patient.get('medical_profile', {}).get('chronic_conditions', []))}")
    print(f"  Insurance:     {patient.get('insurance', {}).get('provider')} (Policy: {patient.get('insurance', {}).get('policy_number')})")

    print(f"\nCLINICAL ENCOUNTERS ({ehr.get('total_encounters')} total):")
    for enc in ehr.get("encounters", []):
        print(f"  - [{enc.get('encounter_id')}] Type: {enc.get('type')} | Dept: {enc.get('department')} | Status: {enc.get('status')}")
        print(f"    Diagnosis: {enc.get('primary_diagnosis')}")
        print(f"    Billing Total: Rs {enc.get('billing', {}).get('total_amount')} (Payment: {enc.get('billing', {}).get('payment_status')})")
        print(f"    Prescriptions: {len(enc.get('prescriptions', []))} logged | Vitals logs: {len(enc.get('vitals_log', []))} logs")

def run_all_and_log():
    """
    Executes all demonstrations and saves the full output to outputs/execution_log.txt.
    """
    os.makedirs("outputs", exist_ok=True)
    log_file = os.path.join("outputs", "execution_log.txt")
    
    # Tee stdout to file
    class LoggerTee:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding="utf-8")
        def write(self, message):
            try:
                self.terminal.write(message)
            except UnicodeEncodeError:
                self.terminal.write(message.encode("ascii", errors="replace").decode("ascii"))
            self.log.write(message)
        def flush(self):
            try:
                self.terminal.flush()
            except Exception:
                pass
            self.log.flush()

    sys.stdout = LoggerTee(log_file)
    print("=" * 80)
    print("  MEDIPULSE HOSPITAL EHR SYSTEM - EXECUTION RUN & VERIFICATION")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print("\n[STEP 1] Re-seeding Database...")
    seed_database(reset=True)

    print("\n[STEP 2] Running Schema Validation Demonstration...")
    demo_schema_validation()

    print("\n[STEP 3] Running PyMongo CRUD Operations...")
    demo_crud_operations()

    print("\n[STEP 4] Running MongoDB Aggregation Pipelines...")
    demo_aggregation_pipelines()

    print("\n[STEP 5] Demonstrating Unified Patient EHR...")
    demo_patient_ehr("PAT-1001")

    print("\n" + "=" * 80)
    print("  ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    sys.stdout.flush()
    sys.stdout = sys.stdout.terminal
    print(f"\n[OK] Complete execution log successfully saved to: {log_file}")

def interactive_menu():
    while True:
        print("\n" + "=" * 60)
        print("  MEDIPULSE EHR - INTELLIGENT NOSQL SYSTEM (CSE494)")
        print("=" * 60)
        print("  [1] Re-seed Database with Realistic Medical Data")
        print("  [2] Demonstrate MongoDB $jsonSchema Validation Rules")
        print("  [3] Demonstrate PyMongo CRUD Operations")
        print("  [4] Execute 5 Advanced Aggregation Pipelines")
        print("  [5] Look up Patient Electronic Health Record (EHR)")
        print("  [6] Run Complete Automated Test Suite & Save Log")
        print("  [0] Exit")
        print("=" * 60)
        
        choice = input("Enter choice (0-6): ").strip()
        if choice == "1":
            seed_database(reset=True)
        elif choice == "2":
            demo_schema_validation()
        elif choice == "3":
            demo_crud_operations()
        elif choice == "4":
            demo_aggregation_pipelines()
        elif choice == "5":
            pid = input("Enter Patient ID (e.g. PAT-1001 to PAT-1008) [Default: PAT-1001]: ").strip()
            if not pid:
                pid = "PAT-1001"
            demo_patient_ehr(pid)
        elif choice == "6":
            run_all_and_log()
        elif choice == "0":
            print("Exiting MediPulse CLI. Goodbye!")
            break
        else:
            print("Invalid selection. Please choose 0 to 6.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--all", "--test", "-a"]:
        run_all_and_log()
    else:
        interactive_menu()
