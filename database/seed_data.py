"""
Database Seeder - Realistic Clinical & Hospital EHR Dataset
CSE494: Intelligent NoSQL Databases - Academic Task 2
"""

from datetime import datetime, timedelta
from database.connection import get_database
from database.validators import apply_validators
from database.indexes import create_indexes
import logging

logger = logging.getLogger("MediPulseSeeder")

PATIENTS_DATA = [
    {
        "patient_id": "PAT-1001",
        "name": "Arjun Sharma",
        "dob": datetime(1985, 4, 12),
        "gender": "Male",
        "blood_group": "B+",
        "contact": {
            "phone": "+91-9876543210",
            "email": "arjun.sharma@example.com",
            "emergency_contact": "+91-9876543211",
            "address": {"street": "42 MG Road", "city": "Bengaluru", "state": "Karnataka", "pincode": "560001"}
        },
        "medical_profile": {
            "allergies": ["Penicillin", "Peanuts"],
            "chronic_conditions": ["Type 2 Diabetes", "Hypertension"],
            "blood_pressure_baseline": "130/85"
        },
        "insurance": {
            "provider": "Star Health",
            "policy_number": "SH-992837",
            "coverage_limit": 500000.0,
            "valid_until": datetime(2027, 12, 31)
        },
        "status": "Active",
        "registered_at": datetime(2023, 1, 15)
    },
    {
        "patient_id": "PAT-1002",
        "name": "Ananya Sen",
        "dob": datetime(1992, 8, 24),
        "gender": "Female",
        "blood_group": "O+",
        "contact": {
            "phone": "+91-9876543212",
            "email": "ananya.sen@example.com",
            "emergency_contact": "+91-9876543213",
            "address": {"street": "18 Park Street", "city": "Kolkata", "state": "West Bengal", "pincode": "700016"}
        },
        "medical_profile": {
            "allergies": ["Sulfa Drugs"],
            "chronic_conditions": ["Bronchial Asthma"],
            "blood_pressure_baseline": "115/75"
        },
        "insurance": {
            "provider": "HDFC ERGO",
            "policy_number": "HD-553190",
            "coverage_limit": 750000.0,
            "valid_until": datetime(2028, 5, 20)
        },
        "status": "Active",
        "registered_at": datetime(2023, 3, 10)
    },
    {
        "patient_id": "PAT-1003",
        "name": "Rajesh Kumar Patel",
        "dob": datetime(1958, 11, 5),
        "gender": "Male",
        "blood_group": "A+",
        "contact": {
            "phone": "+91-9876543214",
            "email": "rajesh.patel@example.com",
            "emergency_contact": "+91-9876543215",
            "address": {"street": "77 Ring Road", "city": "Ahmedabad", "state": "Gujarat", "pincode": "380015"}
        },
        "medical_profile": {
            "allergies": [],
            "chronic_conditions": ["Coronary Artery Disease", "Hypertension", "Dyslipidemia"],
            "blood_pressure_baseline": "145/95"
        },
        "insurance": {
            "provider": "ICICI Lombard",
            "policy_number": "IC-882103",
            "coverage_limit": 1000000.0,
            "valid_until": datetime(2026, 11, 30)
        },
        "status": "Active",
        "registered_at": datetime(2022, 6, 20)
    },
    {
        "patient_id": "PAT-1004",
        "name": "Sunita Verma",
        "dob": datetime(1976, 2, 18),
        "gender": "Female",
        "blood_group": "AB+",
        "contact": {
            "phone": "+91-9876543216",
            "email": "sunita.verma@example.com",
            "emergency_contact": "+91-9876543217",
            "address": {"street": "12 Civil Lines", "city": "Jaipur", "state": "Rajasthan", "pincode": "302006"}
        },
        "medical_profile": {
            "allergies": ["Aspirin"],
            "chronic_conditions": ["Hypothyroidism", "Osteoarthritis"],
            "blood_pressure_baseline": "120/80"
        },
        "insurance": {
            "provider": "Care Health",
            "policy_number": "CH-441029",
            "coverage_limit": 600000.0,
            "valid_until": datetime(2027, 8, 15)
        },
        "status": "Active",
        "registered_at": datetime(2023, 7, 12)
    },
    {
        "patient_id": "PAT-1005",
        "name": "Vikramaditya Roy",
        "dob": datetime(2001, 6, 30),
        "gender": "Male",
        "blood_group": "O-",
        "contact": {
            "phone": "+91-9876543218",
            "email": "vikram.roy@example.com",
            "emergency_contact": "+91-9876543219",
            "address": {"street": "5 South City", "city": "Gurugram", "state": "Haryana", "pincode": "122018"}
        },
        "medical_profile": {
            "allergies": [],
            "chronic_conditions": [],
            "blood_pressure_baseline": "118/78"
        },
        "insurance": {
            "provider": "Niva Bupa",
            "policy_number": "NB-339012",
            "coverage_limit": 500000.0,
            "valid_until": datetime(2028, 1, 10)
        },
        "status": "Active",
        "registered_at": datetime(2024, 2, 1)
    },
    {
        "patient_id": "PAT-1006",
        "name": "Meera Krishnan",
        "dob": datetime(1965, 9, 14),
        "gender": "Female",
        "blood_group": "A-",
        "contact": {
            "phone": "+91-9876543220",
            "email": "meera.k@example.com",
            "emergency_contact": "+91-9876543221",
            "address": {"street": "8 Anna Salai", "city": "Chennai", "state": "Tamil Nadu", "pincode": "600002"}
        },
        "medical_profile": {
            "allergies": ["Ciprofloxacin"],
            "chronic_conditions": ["Chronic Kidney Disease Stage 3", "Hypertension"],
            "blood_pressure_baseline": "140/90"
        },
        "insurance": {
            "provider": "Star Health",
            "policy_number": "SH-771239",
            "coverage_limit": 800000.0,
            "valid_until": datetime(2027, 4, 18)
        },
        "status": "Active",
        "registered_at": datetime(2022, 11, 5)
    },
    {
        "patient_id": "PAT-1007",
        "name": "Kavita Deshmukh",
        "dob": datetime(1995, 12, 1),
        "gender": "Female",
        "blood_group": "B-",
        "contact": {
            "phone": "+91-9876543222",
            "email": "kavita.d@example.com",
            "emergency_contact": "+91-9876543223",
            "address": {"street": "90 FC Road", "city": "Pune", "state": "Maharashtra", "pincode": "411004"}
        },
        "medical_profile": {
            "allergies": [],
            "chronic_conditions": ["Migraine"],
            "blood_pressure_baseline": "110/72"
        },
        "insurance": {
            "provider": "Bajaj Allianz",
            "policy_number": "BA-120934",
            "coverage_limit": 500000.0,
            "valid_until": datetime(2029, 3, 31)
        },
        "status": "Active",
        "registered_at": datetime(2024, 4, 19)
    },
    {
        "patient_id": "PAT-1008",
        "name": "Harpreet Singh",
        "dob": datetime(1980, 3, 22),
        "gender": "Male",
        "blood_group": "AB-",
        "contact": {
            "phone": "+91-9876543224",
            "email": "harpreet.s@example.com",
            "emergency_contact": "+91-9876543225",
            "address": {"street": "14 Model Town", "city": "Jalandhar", "state": "Punjab", "pincode": "144003"}
        },
        "medical_profile": {
            "allergies": ["Ibuprofen"],
            "chronic_conditions": ["Type 2 Diabetes", "Fatty Liver"],
            "blood_pressure_baseline": "135/88"
        },
        "insurance": {
            "provider": "HDFC ERGO",
            "policy_number": "HD-994321",
            "coverage_limit": 1000000.0,
            "valid_until": datetime(2027, 9, 25)
        },
        "status": "Active",
        "registered_at": datetime(2023, 8, 14)
    }
]

DOCTORS_DATA = [
    {
        "doctor_id": "DOC-201",
        "name": "Dr. Priya Nair",
        "specialization": "Interventional Cardiology",
        "department": "Cardiology",
        "qualifications": ["MBBS", "MD Medicine", "DM Cardiology"],
        "experience_years": 14,
        "consultation_fee": 1200.0,
        "availability_days": ["Monday", "Wednesday", "Friday"],
        "contact": {"email": "priya.nair@medipulse.org", "phone": "+91-9123456780"},
        "active": True
    },
    {
        "doctor_id": "DOC-202",
        "name": "Dr. Siddharth Mehta",
        "specialization": "Neurovascular Surgery",
        "department": "Neurology",
        "qualifications": ["MBBS", "MS Surgery", "MCh Neurosurgery"],
        "experience_years": 18,
        "consultation_fee": 1500.0,
        "availability_days": ["Tuesday", "Thursday", "Saturday"],
        "contact": {"email": "siddharth.m@medipulse.org", "phone": "+91-9123456781"},
        "active": True
    },
    {
        "doctor_id": "DOC-203",
        "name": "Dr. Rohini Kulkarni",
        "specialization": "Pulmonology & Critical Care",
        "department": "Pulmonology",
        "qualifications": ["MBBS", "MD Respiratory Medicine"],
        "experience_years": 11,
        "consultation_fee": 900.0,
        "availability_days": ["Monday", "Tuesday", "Thursday", "Friday"],
        "contact": {"email": "rohini.k@medipulse.org", "phone": "+91-9123456782"},
        "active": True
    },
    {
        "doctor_id": "DOC-204",
        "name": "Dr. Vikram Sethi",
        "specialization": "Joint Replacement & Arthroscopy",
        "department": "Orthopedics",
        "qualifications": ["MBBS", "MS Orthopedics", "FACS"],
        "experience_years": 16,
        "consultation_fee": 1100.0,
        "availability_days": ["Wednesday", "Thursday", "Saturday"],
        "contact": {"email": "vikram.sethi@medipulse.org", "phone": "+91-9123456783"},
        "active": True
    },
    {
        "doctor_id": "DOC-205",
        "name": "Dr. Shalini Gupta",
        "specialization": "Internal Medicine & Diabetology",
        "department": "General Medicine",
        "qualifications": ["MBBS", "MD Internal Medicine"],
        "experience_years": 10,
        "consultation_fee": 700.0,
        "availability_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "contact": {"email": "shalini.g@medipulse.org", "phone": "+91-9123456784"},
        "active": True
    },
    {
        "doctor_id": "DOC-206",
        "name": "Dr. Amitava Bose",
        "specialization": "Medical Oncology",
        "department": "Oncology",
        "qualifications": ["MBBS", "MD Medicine", "DM Medical Oncology"],
        "experience_years": 20,
        "consultation_fee": 1800.0,
        "availability_days": ["Monday", "Thursday"],
        "contact": {"email": "amitava.bose@medipulse.org", "phone": "+91-9123456785"},
        "active": True
    }
]

ENCOUNTERS_DATA = [
    {
        "encounter_id": "ENC-5001",
        "patient_id": "PAT-1001",
        "doctor_id": "DOC-201",
        "department": "Cardiology",
        "type": "Inpatient",
        "admission_date": datetime(2026, 9, 10, 8, 30),
        "discharge_date": datetime(2026, 9, 14, 14, 0),
        "status": "Discharged",
        "primary_diagnosis": "Acute Coronary Syndrome",
        "secondary_diagnoses": ["Type 2 Diabetes", "Hypertension"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 9, 10, 9, 0),
                "heart_rate": 96,
                "blood_pressure": {"systolic": 150, "diastolic": 95},
                "spo2": 95,
                "temperature_f": 98.6,
                "recorded_by": "Nurse Deepa"
            },
            {
                "timestamp": datetime(2026, 9, 12, 8, 0),
                "heart_rate": 78,
                "blood_pressure": {"systolic": 128, "diastolic": 82},
                "spo2": 98,
                "temperature_f": 98.4,
                "recorded_by": "Nurse Deepa"
            }
        ],
        "prescriptions": [
            {
                "medication": "Atorvastatin",
                "dosage": "40mg",
                "frequency": "Once daily at bedtime",
                "duration_days": 30,
                "status": "Active"
            },
            {
                "medication": "Aspirin",
                "dosage": "75mg",
                "frequency": "Once daily after food",
                "duration_days": 30,
                "status": "Active"
            },
            {
                "medication": "Metoprolol Succinate",
                "dosage": "25mg",
                "frequency": "Once daily morning",
                "duration_days": 14,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Troponin-I",
                "status": "Completed",
                "result": "0.15 ng/mL",
                "normal_range": "< 0.04 ng/mL",
                "flag": "High"
            },
            {
                "test_name": "HbA1c",
                "status": "Completed",
                "result": "7.8 %",
                "normal_range": "< 5.7 %",
                "flag": "High"
            }
        ],
        "billing": {
            "room_charges": 24000.0,
            "consultation_charges": 6000.0,
            "pharmacy_charges": 4500.0,
            "lab_charges": 5500.0,
            "total_amount": 40000.0,
            "payment_status": "Paid",
            "insurance_claimed": 35000.0
        }
    },
    {
        "encounter_id": "ENC-5002",
        "patient_id": "PAT-1002",
        "doctor_id": "DOC-203",
        "department": "Pulmonology",
        "type": "Emergency",
        "admission_date": datetime(2026, 9, 18, 22, 15),
        "discharge_date": datetime(2026, 9, 20, 11, 30),
        "status": "Discharged",
        "primary_diagnosis": "Acute Severe Bronchial Asthma",
        "secondary_diagnoses": ["Respiratory Distress"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 9, 18, 22, 30),
                "heart_rate": 115,
                "blood_pressure": {"systolic": 135, "diastolic": 85},
                "spo2": 89,
                "temperature_f": 99.1,
                "recorded_by": "Nurse Rajesh"
            },
            {
                "timestamp": datetime(2026, 9, 19, 6, 0),
                "heart_rate": 84,
                "blood_pressure": {"systolic": 120, "diastolic": 80},
                "spo2": 97,
                "temperature_f": 98.6,
                "recorded_by": "Nurse Rajesh"
            }
        ],
        "prescriptions": [
            {
                "medication": "Budecort Inhaler",
                "dosage": "200mcg",
                "frequency": "Twice daily",
                "duration_days": 15,
                "status": "Active"
            },
            {
                "medication": "Deriphyllin Retard",
                "dosage": "150mg",
                "frequency": "Twice daily after meals",
                "duration_days": 7,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Arterial Blood Gas (ABG)",
                "status": "Completed",
                "result": "pH 7.34, pO2 62 mmHg",
                "normal_range": "pO2 75-100 mmHg",
                "flag": "High"
            }
        ],
        "billing": {
            "room_charges": 12000.0,
            "consultation_charges": 2700.0,
            "pharmacy_charges": 3100.0,
            "lab_charges": 3200.0,
            "total_amount": 21000.0,
            "payment_status": "Paid",
            "insurance_claimed": 18000.0
        }
    },
    {
        "encounter_id": "ENC-5003",
        "patient_id": "PAT-1003",
        "doctor_id": "DOC-201",
        "department": "Cardiology",
        "type": "Inpatient",
        "admission_date": datetime(2026, 10, 2, 7, 45),
        "discharge_date": datetime(2026, 10, 7, 16, 0),
        "status": "Discharged",
        "primary_diagnosis": "Congestive Heart Failure",
        "secondary_diagnoses": ["Hypertensive Heart Disease"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 10, 2, 8, 30),
                "heart_rate": 102,
                "blood_pressure": {"systolic": 165, "diastolic": 102},
                "spo2": 92,
                "temperature_f": 98.4,
                "recorded_by": "Nurse Sneha"
            },
            {
                "timestamp": datetime(2026, 10, 5, 10, 0),
                "heart_rate": 76,
                "blood_pressure": {"systolic": 130, "diastolic": 84},
                "spo2": 98,
                "temperature_f": 98.2,
                "recorded_by": "Nurse Sneha"
            }
        ],
        "prescriptions": [
            {
                "medication": "Torsemide",
                "dosage": "20mg",
                "frequency": "Once daily morning",
                "duration_days": 30,
                "status": "Active"
            },
            {
                "medication": "Ramipril",
                "dosage": "5mg",
                "frequency": "Once daily night",
                "duration_days": 30,
                "status": "Active"
            },
            {
                "medication": "Atorvastatin",
                "dosage": "40mg",
                "frequency": "Once daily night",
                "duration_days": 30,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "NT-proBNP",
                "status": "Completed",
                "result": "1850 pg/mL",
                "normal_range": "< 300 pg/mL",
                "flag": "High"
            },
            {
                "test_name": "Serum Creatinine",
                "status": "Completed",
                "result": "1.3 mg/dL",
                "normal_range": "0.7 - 1.2 mg/dL",
                "flag": "High"
            }
        ],
        "billing": {
            "room_charges": 35000.0,
            "consultation_charges": 7500.0,
            "pharmacy_charges": 5800.0,
            "lab_charges": 6700.0,
            "total_amount": 55000.0,
            "payment_status": "Paid",
            "insurance_claimed": 50000.0
        }
    },
    {
        "encounter_id": "ENC-5004",
        "patient_id": "PAT-1004",
        "doctor_id": "DOC-204",
        "department": "Orthopedics",
        "type": "Inpatient",
        "admission_date": datetime(2026, 10, 8, 10, 0),
        "discharge_date": datetime(2026, 10, 12, 12, 0),
        "status": "Discharged",
        "primary_diagnosis": "Severe Osteoarthritis Knee",
        "secondary_diagnoses": ["Hypothyroidism"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 10, 8, 11, 0),
                "heart_rate": 80,
                "blood_pressure": {"systolic": 125, "diastolic": 80},
                "spo2": 99,
                "temperature_f": 98.6,
                "recorded_by": "Nurse Deepa"
            }
        ],
        "prescriptions": [
            {
                "medication": "Paracetamol",
                "dosage": "650mg",
                "frequency": "Thrice daily SOS",
                "duration_days": 10,
                "status": "Active"
            },
            {
                "medication": "Calcium + Vitamin D3",
                "dosage": "500mg",
                "frequency": "Once daily after lunch",
                "duration_days": 60,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Knee Bilateral X-Ray",
                "status": "Completed",
                "result": "Severe joint space narrowing Grade 4",
                "normal_range": "Normal joint space",
                "flag": "High"
            }
        ],
        "billing": {
            "room_charges": 28000.0,
            "consultation_charges": 5500.0,
            "pharmacy_charges": 2200.0,
            "lab_charges": 4300.0,
            "total_amount": 40000.0,
            "payment_status": "Paid",
            "insurance_claimed": 38000.0
        }
    },
    {
        "encounter_id": "ENC-5005",
        "patient_id": "PAT-1005",
        "doctor_id": "DOC-205",
        "department": "General Medicine",
        "type": "Outpatient",
        "admission_date": datetime(2026, 10, 11, 11, 30),
        "discharge_date": datetime(2026, 10, 11, 13, 0),
        "status": "Discharged",
        "primary_diagnosis": "Acute Gastroenteritis",
        "secondary_diagnoses": ["Mild Dehydration"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 10, 11, 11, 45),
                "heart_rate": 88,
                "blood_pressure": {"systolic": 112, "diastolic": 74},
                "spo2": 99,
                "temperature_f": 100.2,
                "recorded_by": "Nurse Rajesh"
            }
        ],
        "prescriptions": [
            {
                "medication": "ORS Solution",
                "dosage": "1 sachet in 1L water",
                "frequency": "Frequently throughout day",
                "duration_days": 3,
                "status": "Active"
            },
            {
                "medication": "Probiotic Capsules",
                "dosage": "1 cap",
                "frequency": "Twice daily after food",
                "duration_days": 5,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Routine Stool Examination",
                "status": "Completed",
                "result": "Few pus cells noted, no ova/cyst",
                "normal_range": "Nil",
                "flag": "Normal"
            }
        ],
        "billing": {
            "room_charges": 1000.0,
            "consultation_charges": 700.0,
            "pharmacy_charges": 650.0,
            "lab_charges": 850.0,
            "total_amount": 3200.0,
            "payment_status": "Paid",
            "insurance_claimed": 0.0
        }
    },
    {
        "encounter_id": "ENC-5006",
        "patient_id": "PAT-1006",
        "doctor_id": "DOC-205",
        "department": "General Medicine",
        "type": "Inpatient",
        "admission_date": datetime(2026, 10, 13, 9, 0),
        "discharge_date": None,
        "status": "Admitted",
        "primary_diagnosis": "Chronic Kidney Disease Exacerbation",
        "secondary_diagnoses": ["Fluid Overload", "Hypertension"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 10, 13, 9, 30),
                "heart_rate": 92,
                "blood_pressure": {"systolic": 158, "diastolic": 98},
                "spo2": 94,
                "temperature_f": 98.7,
                "recorded_by": "Nurse Sneha"
            },
            {
                "timestamp": datetime(2026, 10, 14, 18, 0),
                "heart_rate": 84,
                "blood_pressure": {"systolic": 142, "diastolic": 90},
                "spo2": 96,
                "temperature_f": 98.6,
                "recorded_by": "Nurse Sneha"
            }
        ],
        "prescriptions": [
            {
                "medication": "Furosemide",
                "dosage": "40mg",
                "frequency": "Twice daily IV/Oral",
                "duration_days": 7,
                "status": "Active"
            },
            {
                "medication": "Amlodipine",
                "dosage": "5mg",
                "frequency": "Once daily morning",
                "duration_days": 30,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Serum Creatinine",
                "status": "Completed",
                "result": "2.8 mg/dL",
                "normal_range": "0.6 - 1.1 mg/dL",
                "flag": "High"
            },
            {
                "test_name": "Blood Urea Nitrogen (BUN)",
                "status": "Completed",
                "result": "48 mg/dL",
                "normal_range": "7 - 20 mg/dL",
                "flag": "High"
            }
        ],
        "billing": {
            "room_charges": 18000.0,
            "consultation_charges": 3500.0,
            "pharmacy_charges": 4200.0,
            "lab_charges": 3800.0,
            "total_amount": 29500.0,
            "payment_status": "Pending",
            "insurance_claimed": 25000.0
        }
    },
    {
        "encounter_id": "ENC-5007",
        "patient_id": "PAT-1007",
        "doctor_id": "DOC-202",
        "department": "Neurology",
        "type": "Outpatient",
        "admission_date": datetime(2026, 10, 14, 14, 0),
        "discharge_date": datetime(2026, 10, 14, 15, 30),
        "status": "Discharged",
        "primary_diagnosis": "Chronic Intractable Migraine",
        "secondary_diagnoses": ["Photophobia"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 10, 14, 14, 15),
                "heart_rate": 74,
                "blood_pressure": {"systolic": 118, "diastolic": 76},
                "spo2": 99,
                "temperature_f": 98.4,
                "recorded_by": "Nurse Deepa"
            }
        ],
        "prescriptions": [
            {
                "medication": "Sumatriptan",
                "dosage": "50mg",
                "frequency": "SOS at headache onset",
                "duration_days": 15,
                "status": "Active"
            },
            {
                "medication": "Propranolol",
                "dosage": "40mg",
                "frequency": "Once daily prophylactic",
                "duration_days": 30,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Brain MRI with Angiography",
                "status": "Completed",
                "result": "Normal intracranial vasculature, no lesions",
                "normal_range": "Normal",
                "flag": "Normal"
            }
        ],
        "billing": {
            "room_charges": 1500.0,
            "consultation_charges": 1500.0,
            "pharmacy_charges": 1200.0,
            "lab_charges": 8500.0,
            "total_amount": 12700.0,
            "payment_status": "Paid",
            "insurance_claimed": 10000.0
        }
    },
    {
        "encounter_id": "ENC-5008",
        "patient_id": "PAT-1008",
        "doctor_id": "DOC-206",
        "department": "Oncology",
        "type": "Inpatient",
        "admission_date": datetime(2026, 10, 15, 8, 0),
        "discharge_date": None,
        "status": "Admitted",
        "primary_diagnosis": "Hepatocellular Carcinoma Staging",
        "secondary_diagnoses": ["Fatty Liver", "Type 2 Diabetes"],
        "vitals_log": [
            {
                "timestamp": datetime(2026, 10, 15, 8, 30),
                "heart_rate": 82,
                "blood_pressure": {"systolic": 132, "diastolic": 86},
                "spo2": 97,
                "temperature_f": 98.8,
                "recorded_by": "Nurse Rajesh"
            }
        ],
        "prescriptions": [
            {
                "medication": "Sorafenib",
                "dosage": "200mg",
                "frequency": "Twice daily with meals",
                "duration_days": 30,
                "status": "Active"
            }
        ],
        "lab_orders": [
            {
                "test_name": "Alpha-Fetoprotein (AFP)",
                "status": "Completed",
                "result": "340 ng/mL",
                "normal_range": "< 10 ng/mL",
                "flag": "High"
            },
            {
                "test_name": "Liver Function Panel",
                "status": "Completed",
                "result": "ALT: 85 U/L, AST: 92 U/L",
                "normal_range": "ALT < 45, AST < 40",
                "flag": "High"
            }
        ],
        "billing": {
            "room_charges": 22000.0,
            "consultation_charges": 3600.0,
            "pharmacy_charges": 12500.0,
            "lab_charges": 6800.0,
            "total_amount": 44900.0,
            "payment_status": "Pending",
            "insurance_claimed": 40000.0
        }
    }
]

APPOINTMENTS_DATA = [
    {
        "appointment_id": "APT-9001",
        "patient_id": "PAT-1001",
        "doctor_id": "DOC-201",
        "appointment_time": datetime(2026, 10, 20, 10, 0),
        "reason": "Cardiac follow-up & ECG review",
        "status": "Scheduled"
    },
    {
        "appointment_id": "APT-9002",
        "patient_id": "PAT-1002",
        "doctor_id": "DOC-203",
        "appointment_time": datetime(2026, 10, 22, 14, 30),
        "reason": "Asthma spirometry follow-up",
        "status": "Scheduled"
    },
    {
        "appointment_id": "APT-9003",
        "patient_id": "PAT-1003",
        "doctor_id": "DOC-201",
        "appointment_time": datetime(2026, 10, 24, 11, 0),
        "reason": "Echocardiogram review & titration",
        "status": "Scheduled"
    },
    {
        "appointment_id": "APT-9004",
        "patient_id": "PAT-1004",
        "doctor_id": "DOC-204",
        "appointment_time": datetime(2026, 10, 25, 9, 30),
        "reason": "Post-discharge knee mobility assessment",
        "status": "Scheduled"
    },
    {
        "appointment_id": "APT-9005",
        "patient_id": "PAT-1005",
        "doctor_id": "DOC-205",
        "appointment_time": datetime(2026, 10, 18, 16, 0),
        "reason": "Gastroenteritis recovery check",
        "status": "Scheduled"
    },
    {
        "appointment_id": "APT-9006",
        "patient_id": "PAT-1007",
        "doctor_id": "DOC-202",
        "appointment_time": datetime(2026, 10, 28, 15, 0),
        "reason": "Migraine diary review",
        "status": "Scheduled"
    }
]

def seed_database(reset: bool = True):
    """
    Applies validators, creates indexes, and populates the database with initial documents.
    """
    db = get_database()
    
    if reset:
        logger.info("Dropping existing collections to perform clean re-seed...")
        for coll in ["patients", "doctors", "encounters", "appointments"]:
            db[coll].drop()

    # 1. Apply Validators
    logger.info("Applying $jsonSchema validation rules...")
    apply_validators(db)

    # 2. Create Indexes
    logger.info("Creating single, compound, and text indexes...")
    create_indexes(db)

    # 3. Seed Collections
    logger.info("Inserting initial dataset...")
    db.patients.insert_many(PATIENTS_DATA)
    db.doctors.insert_many(DOCTORS_DATA)
    db.encounters.insert_many(ENCOUNTERS_DATA)
    db.appointments.insert_many(APPOINTMENTS_DATA)

    logger.info(f"Seeding completed successfully! Counts: Patients={db.patients.count_documents({})}, Doctors={db.doctors.count_documents({})}, Encounters={db.encounters.count_documents({})}, Appointments={db.appointments.count_documents({})}")
    return True

if __name__ == "__main__":
    seed_database(reset=True)
