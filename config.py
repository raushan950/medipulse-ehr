"""
MediPulse Hospital & EHR System - Configuration
CSE494: Intelligent NoSQL Databases - Academic Task 2
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "medipulse_db")

# Collection Names
PATIENTS_COLLECTION = "patients"
DOCTORS_COLLECTION = "doctors"
ENCOUNTERS_COLLECTION = "encounters"
DEPARTMENTS_COLLECTION = "departments"
APPOINTMENTS_COLLECTION = "appointments"
