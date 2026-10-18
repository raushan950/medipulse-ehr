# MediPulse EHR — Intelligent NoSQL Healthcare Management Platform
### Lovely Professional University (LPU) — CSE494: INTELLIGENT NOSQL DATABASES
**Academic Task 2 (Project) • Maximum Marks: 30**

---

## 🌟 Overview
**MediPulse EHR** is a full-stack, production-grade healthcare and Electronic Health Record (EHR) system built on **MongoDB 8.2** and **Python 3.12 (PyMongo 4.19)**. It models multi-specialty patient admissions, high-frequency vitals telemetry, complex diagnostic orders, and prescriptions using an optimized hybrid document architecture (embedded vitals/prescriptions + referenced patients/doctors).

---

## 🚀 Key Features

1. **MongoDB Engine-Level Schema Validation ($jsonSchema):**
   - Enforces strict BSON data types, required keys, enum boundaries (e.g. 8 standard blood groups `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`), and regex patterns (`^\+?[0-9\s\-]{10,15}$`).
   - Rejects non-compliant documents with `WriteError: Document failed validation` (Error Code: 121).

2. **Optimized Indexing Strategy:**
   - Single-field unique indexes on IDs (`patient_id`, `doctor_id`, `encounter_id`, `appointment_id`).
   - Compound indexes: `(department, admission_date)` and `(contact.address.city, status)`.
   - Full-text search indexes on patient names, primary diagnoses, and chronic conditions.
   - Multikey index on embedded `vitals_log.timestamp`.

3. **Comprehensive PyMongo CRUD Services:**
   - **Create:** `insert_one`, `insert_many`.
   - **Read:** Equality queries, compound filters with `$and`/`$or`, text search with score ranking, and nested array queries with `$elemMatch`.
   - **Update:** Operators `$set`, `$push` (logging vitals), `$addToSet` (recording unique allergies), atomic `$set` + `$inc` (encounter discharge and billing).
   - **Delete:** `delete_one`, `delete_many`.

4. **5 Advanced Clinical Aggregation Pipelines:**
   - **Pipeline 1 (Departmental Financials):** `$match` $\rightarrow$ `$group` $\rightarrow$ `$sort` $\rightarrow$ `$project`
   - **Pipeline 2 (Doctor Performance & Cross-Collection Join):** `$lookup` $\rightarrow$ `$unwind` $\rightarrow$ `$group` $\rightarrow$ `$sort` $\rightarrow$ `$project`
   - **Pipeline 3 (Medication Prescription Trends):** `$unwind` $\rightarrow$ `$group` $\rightarrow$ `$sort` $\rightarrow$ `$limit` $\rightarrow$ `$project`
   - **Pipeline 4 (Multi-Faceted Executive Dashboard):** Single-pass parallel aggregation using `$facet`
   - **Pipeline 5 (Demographic Risk & Age Buckets):** Dynamic age computation (`$dateDiff`) $\rightarrow$ `$bucket` $\rightarrow$ `$project`

5. **Two Execution & Demonstration Interfaces:**
   - **Clinical Workbench:** Patient search, upcoming follow-ups, encounter charts, visit notes, vitals, prescriptions, and appointment scheduling.
   - **Clinic Operations:** Start encounters, review active patients, and discharge with final bill calculation.
   - **Database Lab:** Reports, query examples, and schema validation are available separately from everyday clinical tasks.
   - **Interactive CLI Runner (`cli.py`):** Terminal-based runner formatted with ASCII tables for viva demonstrations.

---

## 📂 Project Directory Structure

```
c:\Users\DELL\OneDrive\Desktop\Nosql\
├── app.py                         # Flask Web Server & REST API endpoints
├── cli.py                         # Interactive Terminal CLI for Viva & Grading
├── config.py                      # Database Configuration & Collection Names
├── database/
│   ├── connection.py              # PyMongo Client Singleton with Connection Pooling
│   ├── validators.py              # MongoDB $jsonSchema Collection Definitions
│   ├── indexes.py                 # Index Creation Routines
│   └── seed_data.py               # Realistic Synthetic Healthcare Data Seeder
├── services/
│   ├── crud_service.py            # Complete CRUD Operations Layer
│   └── aggregation_service.py     # 5 Multi-Stage Aggregation Pipelines
├── static/
│   ├── css/style.css              # Glassmorphic Dark-Mode Design System
│   └── js/main.js                 # Chart.js Visualizations & AJAX Logic
├── templates/
│   └── index.html                 # Responsive Web Dashboard Interface
├── tests/
│   └── test_medipulse.py          # Automated 18-Test Unit & Integration Suite
├── outputs/
│   └── execution_log.txt          # Saved Console Output of Full Test Run
├── docs/
│   └── screenshots/               # Verified UI & Execution Screenshots
├── PROJECT_REPORT.md              # Comprehensive Academic Project Report
├── VIVA_QUESTIONS_AND_ANSWERS.md  # 25+ Viva Voce Questions & Solutions
└── README.md                      # This Quickstart Guide
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.12.10)
- MongoDB Server 7.0+ or 8.0+ running on `localhost:27017`

### Install Dependencies
```bash
pip install pymongo flask flask-cors tabulate rich python-dotenv
```

---

## 🎮 How to Run

### 1. Launch the Web Application (Interactive Dashboard)
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```
On first launch, create the clinic administrator account in the browser. Choose a password with at least 12 characters. The account is stored in MongoDB with a password hash; subsequent visits require sign-in. The configured database defaults to `medipulse_db` on `mongodb://localhost:27017/`. A fresh database is initialized with starter records once; existing patient data is not reseeded automatically.

Set `MONGODB_URI` and `DATABASE_NAME` environment variables to use another MongoDB deployment/database. Set `FLASK_SECRET_KEY` to a persistent secret when running beyond local development.

**Web App Highlights:**
- **Clinical workspace:** Search by patient name, ID, or condition; narrow by blood group; open the patient's encounter history.
- **Document care:** On an active encounter, save a visit note, record vitals, or add a prescription. Changes are written to MongoDB and shown in the chart.
- **Follow up:** Schedule and cancel appointments; the upcoming-visit queue updates from saved records.
- **Book from the visit queue:** Select the + beside Upcoming visits, choose a patient and clinician, set the date/time, enter a reason, and save.
- **Past visit records:** Discharge changes the encounter status and final bill; it does not delete the encounter or patient. Find discharged records under **Admissions → Past visits**, then open the patient's chart for full history.
- **Clinic operations:** Register and update patients, create encounters, and discharge patients with pharmacy charges. Records linked to clinical history cannot be deleted.
- **Admin access:** Sign-in protects dashboard and API operations; use **Sign out** in the header to end the session.

---

### 2. Run the Interactive Terminal CLI (For Viva Demonstration)
```bash
python cli.py
```
Provides an interactive menu:
```
[1] Re-seed Database with Realistic Medical Data
[2] Demonstrate MongoDB $jsonSchema Validation Rules
[3] Demonstrate PyMongo CRUD Operations
[4] Execute 5 Advanced Aggregation Pipelines
[5] Look up Patient Electronic Health Record (EHR)
[6] Run Complete Automated Test Suite & Save Log
[0] Exit
```

To run all operations and save the output log automatically:
```bash
python cli.py --all
```

---

### 3. Run Automated Unit Tests
```bash
set DATABASE_NAME=medipulse_test&& python -m unittest tests/test_medipulse.py
```
The tests reset their configured database before seeding, so use a separate `DATABASE_NAME` as shown. The suite covers schema validation, patient and clinical CRUD, appointments, discharge billing, and all 5 aggregation pipelines.

---

## 🚀 Production Deployment Guide

MediPulse EHR includes turnkey configurations for cloud, containerized, and local production deployments:

### Option A: Local / Intranet Production WSGI (Windows / Linux)
Run with the high-performance multi-threaded WSGI server (`waitress`):
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch production server
python run_production.py
```
By default, the server listens on `http://0.0.0.0:5000/`, allowing access across your local network.

### Option B: Containerized Deployment (Docker & Docker Compose)
Launch both the Flask Web App and MongoDB 8.0 with isolated networking and persistent data volumes in one command:
```bash
docker compose up --build -d
```
- Web Application: `http://localhost:5000/`
- MongoDB Database: `localhost:27017` (auto-healthchecked and initialized)

### Option C: Cloud Deployment (Render / Railway / Heroku + MongoDB Atlas)
1. **Database:** Create a free M0 cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and copy the connection string.
2. **Repository:** Push this directory to your GitHub account.
3. **Deploy on Render:**
   - Create a new **Web Service** on [Render](https://render.com/) pointing to your repository (or use the included `render.yaml` Blueprint).
   - Set the Build Command: `pip install -r requirements.txt`
   - Set the Start Command: `gunicorn app:app`
   - Add Environment Variable:
     - `MONGODB_URI`: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
     - `FLASK_SECRET_KEY`: `<secure_random_hex_string>`
     - `DATABASE_NAME`: `medipulse_db`

---

## 📑 Academic Documentation Included
- [PROJECT_REPORT.md](file:///c:/Users/DELL/OneDrive/Desktop/Nosql/PROJECT_REPORT.md): Complete, submission-ready project report with ER diagrams, data dictionary, query catalog, and outputs.
- [VIVA_QUESTIONS_AND_ANSWERS.md](file:///c:/Users/DELL/OneDrive/Desktop/Nosql/VIVA_QUESTIONS_AND_ANSWERS.md): Complete guide with 25+ viva questions categorized by Bloom's taxonomy and examiner query modification solutions.
- [outputs/execution_log.txt](file:///c:/Users/DELL/OneDrive/Desktop/Nosql/outputs/execution_log.txt): Complete terminal execution log.
- [docs/screenshots/](file:///c:/Users/DELL/OneDrive/Desktop/Nosql/docs/screenshots): 9 captured screenshots demonstrating UI, charts, modals, query output, and validation engine rejections.
