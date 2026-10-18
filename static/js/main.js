/**
 * MediPulse Hospital & EHR - Frontend Interaction & Visualization Script
 * CSE494: Intelligent NoSQL Databases - Academic Task 2
 */

let deptChart = null;
let docChart = null;
let medChart = null;
let activePatientId = null;
let pendingDeletePatientId = null;
let admissionView = "active";
let appointmentFromChart = false;

// Predefined query code snippets for Tab 3
const QUERY_SNIPPETS = {
  agg1: {
    code: `// PIPELINE 1: Department Financial Analytics
pipeline = [
  { "$match": { "billing.total_amount": { "$exists": True, "$gt": 0 } } },
  { "$group": {
      "_id": "$department",
      "total_encounters": { "$sum": 1 },
      "total_revenue": { "$sum": "$billing.total_amount" },
      "avg_revenue_per_encounter": { "$avg": "$billing.total_amount" },
      "total_insurance_claimed": { "$sum": "$billing.insurance_claimed" },
      "inpatient_count": { "$sum": { "$cond": [{ "$eq": ["$type", "Inpatient"] }, 1, 0] } }
  }},
  { "$sort": { "total_revenue": -1 } },
  { "$project": {
      "department": "$_id",
      "total_encounters": 1,
      "total_revenue": { "$round": ["$total_revenue", 2] },
      "avg_revenue_per_encounter": { "$round": ["$avg_revenue_per_encounter", 2] }
  }}
]
results = db.encounters.aggregate(pipeline)`,
    endpoint: "/api/analytics/departments"
  },
  agg2: {
    code: `// PIPELINE 2: Doctor Workload & Cross-Collection Join ($lookup)
pipeline = [
  { "$lookup": {
      "from": "doctors",
      "localField": "doctor_id",
      "foreignField": "doctor_id",
      "as": "doctor_info"
  }},
  { "$unwind": "$doctor_info" },
  { "$group": {
      "_id": {
          "doctor_id": "$doctor_id",
          "doctor_name": "$doctor_info.name",
          "specialization": "$doctor_info.specialization",
          "department": "$doctor_info.department"
      },
      "total_encounters": { "$sum": 1 },
      "unique_patients_treated": { "$addToSet": "$patient_id" },
      "total_billing": { "$sum": "$billing.total_amount" }
  }},
  { "$sort": { "total_billing": -1 } }
]
results = db.encounters.aggregate(pipeline)`,
    endpoint: "/api/analytics/doctors"
  },
  agg3: {
    code: `// PIPELINE 3: Medication Prescription Frequency ($unwind)
pipeline = [
  { "$unwind": "$prescriptions" },
  { "$group": {
      "_id": "$prescriptions.medication",
      "prescription_count": { "$sum": 1 },
      "avg_duration_days": { "$avg": "$prescriptions.duration_days" },
      "prescribing_departments": { "$addToSet": "$department" }
  }},
  { "$sort": { "prescription_count": -1 } },
  { "$limit": 5 }
]
results = db.encounters.aggregate(pipeline)`,
    endpoint: "/api/analytics/medications"
  },
  agg4: {
    code: `// PIPELINE 4: Multi-Faceted Executive Hospital Overview ($facet)
pipeline = [
  { "$facet": {
      "encounter_type_distribution": [
          { "$group": { "_id": "$type", "count": { "$sum": 1 } } }
      ],
      "financial_overview": [
          { "$group": {
              "_id": None,
              "gross_revenue": { "$sum": "$billing.total_amount" },
              "avg_bill": { "$avg": "$billing.total_amount" }
          }}
      ],
      "critical_vitals_count": [
          { "$unwind": "$vitals_log" },
          { "$match": { "$or": [{ "vitals_log.heart_rate": { "$gte": 100 } }] } },
          { "$count": "alert_readings" }
      ]
  }}
]
results = db.encounters.aggregate(pipeline)`,
    endpoint: "/api/analytics/executive-kpis"
  },
  agg5: {
    code: `// PIPELINE 5: Demographic Risk & Age Buckets ($bucket)
pipeline = [
  { "$addFields": {
      "age": { "$dateDiff": { "startDate": "$dob", "endDate": "$$NOW", "unit": "year" } }
  }},
  { "$bucket": {
      "groupBy": "$age",
      "boundaries": [0, 30, 50, 70, 120],
      "default": "Unknown",
      "output": {
          "count": { "$sum": 1 },
          "avg_age": { "$avg": "$age" },
          "total_conditions": { "$sum": { "$size": { "$ifNull": ["$medical_profile.chronic_conditions", []] } } }
      }
  }}
]
results = db.patients.aggregate(pipeline)`,
    endpoint: "/api/analytics/age-stratification"
  },
  crud_blood: {
    code: `// CRUD: Equality Filter on Blood Group B+ with Projection
cursor = db.patients.find(
    {"blood_group": "B+"},
    {"_id": 0, "patient_id": 1, "name": 1, "blood_group": 1, "contact.phone": 1}
)`,
    endpoint: "/api/patients?blood_group=B%2B"
  },
  crud_text: {
    code: `// CRUD: Full-Text Search on Indexed Medical Profile ($text)
cursor = db.patients.find(
    {"$text": {"$search": "Diabetes"}},
    {"_id": 0, "patient_id": 1, "name": 1, "medical_profile": 1}
)`,
    endpoint: "/api/patients?search=Diabetes"
  },
  crud_elem: {
    code: `// CRUD: $elemMatch Query on Nested Array of Vitals
cursor = db.encounters.find(
    {"vitals_log": {"$elemMatch": {"heart_rate": {"$gte": 100}}}},
    {"_id": 0, "encounter_id": 1, "primary_diagnosis": 1, "vitals_log.$": 1}
)`,
    endpoint: "/api/encounters/abnormal-vitals?min_hr=100"
  }
};

// Sandbox presets for Tab 4
const SANDBOX_PRESETS = {
  valid: {
    type: "patient",
    document: {
      patient_id: "PAT-9501",
      name: "Tanya Sen",
      dob: "1994-08-14",
      gender: "Female",
      blood_group: "O+",
      contact: {
        phone: "+91-9876543299",
        email: "tanya.sen@example.com",
        address: { street: "12 Lake Road", city: "Kolkata", state: "West Bengal", pincode: "700029" }
      },
      status: "Active"
    }
  },
  invalid_blood: {
    type: "patient",
    document: {
      patient_id: "PAT-9502",
      name: "Faulty Blood Group Patient",
      dob: "1990-01-01",
      gender: "Male",
      blood_group: "Z+", // Violates enum boundary
      contact: {
        phone: "+91-9876543299",
        email: "faulty.bg@example.com"
      },
      status: "Active"
    }
  },
  invalid_phone: {
    type: "patient",
    document: {
      patient_id: "PAT-9503",
      name: "Bad Phone Patient",
      dob: "1990-01-01",
      gender: "Male",
      blood_group: "A+",
      contact: {
        phone: "phone-123", // Violates regex: ^\+?[0-9\s\-]{10,15}$
        email: "badphone@example.com"
      },
      status: "Active"
    }
  },
  invalid_doctor_fee: {
    type: "doctor",
    document: {
      doctor_id: "DOC-991",
      name: "Dr. Underpaid",
      specialization: "General Practice",
      department: "General Medicine",
      consultation_fee: 40.0 // Violates $minimum: 100 constraint
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initSystem();
  setupEventListeners();
  handleQuerySelect("agg1");
  loadSandboxPreset("valid");
});

async function initSystem() {
  await fetchSystemHealth();
  await loadExecutiveKPIs();
  await loadPatients();
  await loadActiveAdmissions();
  await loadAppointments();
}

function setupEventListeners() {
  document.getElementById("btnLogout").addEventListener("click", logoutAdmin);
  document.getElementById("dischargePharmacyCost").addEventListener("input", updateDischargeTotal);
}

// ==========================================
// TAB SWITCHING
// ==========================================
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));

  const targetContent = document.getElementById(`tab-${tabId}`);
  if (targetContent) targetContent.classList.add("active");

  const matchingBtn = Array.from(document.querySelectorAll(".tab-btn")).find(b =>
    b.getAttribute("onclick") && b.getAttribute("onclick").includes(tabId)
  );
  if (matchingBtn) matchingBtn.classList.add("active");
  if (tabId === "analytics") loadAnalyticsCharts();
}

// ==========================================
// SYSTEM HEALTH & KPIS
// ==========================================
async function fetchSystemHealth() {
  try {
    const res = await fetch("/api/system/health");
    const json = await res.json();
    if (json.success) {
      document.getElementById("dbStatusText").textContent = `MongoDB • ${json.data.database} • ${json.data.patient_count} patients`;
    }
  } catch (err) {
    document.getElementById("dbStatusText").textContent = "Connection Error";
    document.getElementById("dbStatus").style.color = "var(--accent-rose)";
  }
}

async function loadExecutiveKPIs() {
  try {
    const [healthResponse, activeResponse, appointmentsResponse, doctorsResponse] = await Promise.all([
      fetch("/api/system/health"), fetch("/api/encounters/active"),
      fetch("/api/appointments/upcoming"), fetch("/api/doctors")
    ]);
    const [health, active, appointments, doctors] = await Promise.all([
      healthResponse.json(), activeResponse.json(), appointmentsResponse.json(), doctorsResponse.json()
    ]);
    if (!health.success || !active.success || !appointments.success || !doctors.success) return;
    document.getElementById("kpiRevenue").textContent = health.data.patient_count;
    document.getElementById("kpiAdmissions").textContent = active.count;
    document.getElementById("kpiStatus").textContent = "Patients currently receiving care";
    document.getElementById("kpiAlerts").textContent = appointments.data.length;
    document.getElementById("kpiDoctors").textContent = doctors.data.length;
  } catch (e) {
    console.error("Failed to load clinical overview", e);
  }
}

// ==========================================
// ANALYTICS CHARTS (Pipelines 1, 2, 3, 5)
// ==========================================
async function loadAnalyticsCharts() {
  // Chart 1: Department Revenue & Total Encounters
  try {
    const res = await fetch("/api/analytics/departments");
    const json = await res.json();
    if (json.success) {
      const labels = json.data.map(d => d.department);
      const revenues = json.data.map(d => d.total_revenue);
      const encounters = json.data.map(d => d.total_encounters);

      const ctx = document.getElementById("deptRevenueChart").getContext("2d");
      if (deptChart) deptChart.destroy();
      deptChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Gross Revenue (₹)",
              data: revenues,
              backgroundColor: "rgba(6, 182, 212, 0.7)",
              borderColor: "#06b6d4",
              borderWidth: 1.5,
              borderRadius: 6,
              yAxisID: 'y'
            },
            {
              label: "Encounters",
              data: encounters,
              type: "line",
              borderColor: "#f59e0b",
              backgroundColor: "#f59e0b",
              borderWidth: 2,
              pointRadius: 4,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
            y: {
              type: 'linear',
              position: 'left',
              ticks: { color: "#94a3b8" },
              grid: { color: "rgba(255, 255, 255, 0.05)" }
            },
            y1: {
              type: 'linear',
              position: 'right',
              ticks: { color: "#f59e0b", precision: 0 },
              grid: { drawOnChartArea: false }
            }
          },
          plugins: {
            legend: { labels: { color: "#e2e8f0" } }
          }
        }
      });
    }
  } catch (e) {
    console.error("Dept chart error", e);
  }

  // Chart 2: Doctor Revenue Performance ($lookup)
  try {
    const res = await fetch("/api/analytics/doctors");
    const json = await res.json();
    if (json.success) {
      const names = json.data.map(d => d.doctor_name);
      const revenue = json.data.map(d => d.total_billing_generated);

      const ctx = document.getElementById("doctorRevenueChart").getContext("2d");
      if (docChart) docChart.destroy();
      docChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: names,
          datasets: [{
            label: "Generated Billing (₹)",
            data: revenue,
            backgroundColor: "rgba(59, 130, 246, 0.7)",
            borderColor: "#3b82f6",
            borderWidth: 1.5,
            borderRadius: 6
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255, 255, 255, 0.05)" } },
            y: { ticks: { color: "#94a3b8" }, grid: { display: false } }
          },
          plugins: {
            legend: { labels: { color: "#e2e8f0" } }
          }
        }
      });
    }
  } catch (e) {
    console.error("Doctor chart error", e);
  }

  // Chart 3: Top Prescribed Medications ($unwind)
  try {
    const res = await fetch("/api/analytics/medications");
    const json = await res.json();
    if (json.success) {
      const meds = json.data.map(d => d.medication);
      const counts = json.data.map(d => d.prescription_count);

      const ctx = document.getElementById("medicationChart").getContext("2d");
      if (medChart) medChart.destroy();
      medChart = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: meds,
          datasets: [{
            data: counts,
            backgroundColor: [
              "rgba(6, 182, 212, 0.8)",
              "rgba(59, 130, 246, 0.8)",
              "rgba(139, 92, 246, 0.8)",
              "rgba(16, 185, 129, 0.8)",
              "rgba(245, 158, 11, 0.8)"
            ],
            borderColor: "#0a0d14",
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { color: "#e2e8f0" } }
          }
        }
      });
    }
  } catch (e) {
    console.error("Med chart error", e);
  }

  // Table: Age Stratification ($bucket)
  try {
    const res = await fetch("/api/analytics/age-stratification");
    const json = await res.json();
    if (json.success) {
      const tbody = document.querySelector("#ageStratTable tbody");
      tbody.innerHTML = "";
      json.data.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${row.age_bracket}</strong></td>
          <td>${row.patient_count}</td>
          <td>${row.average_age} yrs</td>
          <td>${row.total_chronic_conditions}</td>
          <td><span class="badge-tag">${row.avg_chronic_conditions_per_patient}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error("Age strat table error", e);
  }
}

// ==========================================
// PATIENT EHR EXPLORER
// ==========================================
async function loadPatients(queryUrl = "/api/patients") {
  const container = document.getElementById("patientsContainer");
  container.innerHTML = "<div style='color: var(--text-muted);'>Loading patients from MongoDB...</div>";

  try {
    const res = await fetch(queryUrl);
    const json = await res.json();
    if (json.success) {
      container.innerHTML = "";
      if (json.data.length === 0) {
        container.innerHTML = "<div style='color: var(--text-muted); grid-column: 1/-1;'>No patients matched your query.</div>";
        return;
      }

      json.data.forEach(p => {
        const card = document.createElement("div");
        card.className = "patient-card";

        const bgClass = p.blood_group.includes("+") ? "red" : "blue";
        const conditions = p.medical_profile?.chronic_conditions || [];
        const dobStr = p.dob ? new Date(p.dob.$date || p.dob).toLocaleDateString() : "N/A";

        card.innerHTML = `
          <div class="patient-card-header">
            <div>
              <span style="font-size: 0.75rem; color: var(--accent-cyan); font-family: monospace;">${p.patient_id}</span>
              <h4>${p.name}</h4>
            </div>
            <span class="bg-pill ${bgClass}">${p.blood_group}</span>
          </div>
          <div class="patient-meta">
            <div>DOB: ${dobStr} • ${p.gender}</div>
            <div>Phone: ${p.contact?.phone || "N/A"}</div>
            <div>City: ${p.contact?.address?.city || "N/A"}</div>
          </div>
          <div class="tags-list">
            ${conditions.map(c => `<span class="tag-item">${c}</span>`).join("") || "<span style='font-size:0.75rem; color:var(--text-dim)'>No chronic conditions</span>"}
          </div>
          <button class="btn btn-outline btn-sm patient-chart-button" onclick="openEhrModal('${p.patient_id}')">Open patient chart</button>
        `;
        container.appendChild(card);
      });
    }
  } catch (e) {
    container.innerHTML = `<div style='color: var(--accent-rose);'>Failed to load patients: ${e.message}</div>`;
  }
}

function patientSearchUrl() {
  const params = new URLSearchParams();
  const search = document.getElementById("patientSearchInput").value.trim();
  const bloodGroup = document.getElementById("bloodGroupFilter").value;
  if (search) params.set("search", search);
  if (bloodGroup) params.set("blood_group", bloodGroup);
  return params.size ? `/api/patients?${params.toString()}` : "/api/patients";
}

async function loadAppointments() {
  const queue = document.getElementById("appointmentQueue");
  if (!queue) return;
  try {
    const response = await fetch("/api/appointments/upcoming");
    const json = await response.json();
    if (!response.ok || !json.success) throw new Error(json.error || "Could not load upcoming visits.");
    queue.replaceChildren();
    document.getElementById("appointmentQueueMeta").textContent = `${json.data.length} scheduled`;
    if (!json.data.length) {
      queue.innerHTML = '<p class="empty-state">No upcoming visits. Schedule a follow-up from a patient chart.</p>';
      return;
    }
    json.data.forEach(appointment => {
      const item = document.createElement("article");
      item.className = "appointment-item";
      const date = new Date(appointment.appointment_time?.$date || appointment.appointment_time);
      const time = document.createElement("time");
      time.dateTime = date.toISOString();
      time.textContent = date.toLocaleString([], { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
      const details = document.createElement("div");
      details.className = "appointment-details";
      const patient = document.createElement("strong");
      patient.textContent = appointment.patient_name;
      const reason = document.createElement("span");
      reason.textContent = appointment.reason || "Follow-up";
      const clinician = document.createElement("small");
      clinician.textContent = `${appointment.doctor_name}${appointment.department ? ` · ${appointment.department}` : ""}`;
      details.append(patient, reason, clinician);
      const cancel = document.createElement("button");
      cancel.className = "icon-button icon-button-muted";
      cancel.type = "button";
      cancel.title = "Cancel appointment";
      cancel.setAttribute("aria-label", `Cancel appointment ${appointment.appointment_id}`);
      cancel.textContent = "×";
      cancel.addEventListener("click", () => cancelAppointment(appointment.appointment_id));
      item.append(time, details, cancel);
      queue.appendChild(item);
    });
  } catch (error) {
    queue.innerHTML = `<p class="empty-state error-text">${error.message}</p>`;
  }
}

async function cancelAppointment(appointmentId) {
  try {
    const response = await fetch(`/api/appointments/${encodeURIComponent(appointmentId)}/cancel`, { method: "POST" });
    const json = await response.json();
    if (!response.ok || !json.success) throw new Error(json.error || "Could not cancel appointment.");
    await Promise.all([loadAppointments(), loadExecutiveKPIs()]);
    if (activePatientId) await openEhrModal(activePatientId);
  } catch (error) {
    alert(error.message);
  }
}

async function loadActiveAdmissions() {
  const tbody = document.getElementById("activeAdmissionsBody");
  if (!tbody) return;
  const isPast = admissionView === "past";
  tbody.innerHTML = `<tr><td colspan="7">Loading ${isPast ? "past visits" : "active encounters"}...</td></tr>`;

  try {
    const res = await fetch(isPast ? "/api/encounters/past" : "/api/encounters/active");
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || "Could not load encounters.");
    tbody.innerHTML = "";
    if (!json.data.length) {
      tbody.innerHTML = `<tr><td colspan="7">${isPast ? "No discharged visits on file." : "No active encounters."}</td></tr>`;
      return;
    }

    json.data.forEach(encounter => {
      const patient = encounter.patient_info || {};
      const doctor = encounter.doctor_info || {};
      const vital = encounter.latest_vital || {};
      const patientName = encounter.patient_name || patient.name || encounter.patient_id;
      const patientLink = `<button class="table-link" onclick="openEhrModal('${encodeURIComponent(encounter.patient_id)}')">${escapeHTML(patientName)}<small>${escapeHTML(encounter.patient_id)}</small></button>`;
      const row = document.createElement("tr");
      if (isPast) {
        const dischargeDate = encounter.discharge_date ? new Date(encounter.discharge_date.$date || encounter.discharge_date).toLocaleDateString() : "—";
        row.innerHTML = `
          <td>${escapeHTML(encounter.encounter_id)}</td>
          <td>${patientLink}</td>
          <td>${escapeHTML(encounter.department || "N/A")}</td>
          <td>${escapeHTML(encounter.doctor_name || encounter.doctor_id)}</td>
          <td>${escapeHTML(dischargeDate)}</td>
          <td>${formatCurrency(Number(encounter.billing?.total_amount || 0))}</td>
          <td><button class="btn btn-outline btn-sm" onclick="openEhrModal('${encodeURIComponent(encounter.patient_id)}')">Open chart</button></td>
        `;
      } else {
        row.innerHTML = `
          <td>${escapeHTML(encounter.encounter_id)}</td>
          <td>${patientLink}</td>
          <td>${escapeHTML(encounter.department || "N/A")}</td>
          <td>${escapeHTML(doctor.name || encounter.doctor_id)}</td>
          <td>${vital.heart_rate ? `${vital.heart_rate} bpm` : "No readings"}${vital.spo2 ? ` / ${vital.spo2}% SpO₂` : ""}</td>
          <td>${escapeHTML(encounter.primary_diagnosis || "N/A")}</td>
          <td><button class="btn btn-danger btn-sm" onclick="openDischargeModal('${encodeURIComponent(encounter.encounter_id)}', ${Number(encounter.billing?.total_amount || 0)})">Discharge</button></td>
        `;
      }
      tbody.appendChild(row);
    });
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="7">Could not load admissions: ${error.message}</td></tr>`;
  }
}

function setAdmissionView(view) {
  admissionView = view === "past" ? "past" : "active";
  const isPast = admissionView === "past";
  document.getElementById("showActiveEncounters").classList.toggle("active", !isPast);
  document.getElementById("showPastEncounters").classList.toggle("active", isPast);
  document.getElementById("admissionListTitle").textContent = isPast ? "Past discharged visits" : "Active encounters";
  document.getElementById("admissionListDescription").textContent = isPast
    ? "Discharged records remain in MongoDB and can be reopened from the patient's chart."
    : "Patients currently receiving care. Discharged visits remain in the past encounter archive.";
  document.getElementById("admissionVitalsHeader").textContent = isPast ? "Discharged" : "Latest vitals";
  document.getElementById("admissionDiagnosisHeader").textContent = isPast ? "Final bill" : "Diagnosis";
  document.getElementById("admissionActionsHeader").textContent = isPast ? "Record" : "Actions";
  document.getElementById("startEncounterButton").hidden = isPast;
  loadActiveAdmissions();
}

function openDischargeModal(encounterId, currentBill) {
  document.getElementById("dischargeEncounterId").value = encounterId;
  document.getElementById("dischargeEncounterLabel").textContent = `Encounter ${encounterId}`;
  document.getElementById("dischargeCurrentBill").textContent = formatCurrency(currentBill);
  document.getElementById("dischargePharmacyCost").value = "0";
  document.getElementById("dischargeAlert").style.display = "none";
  updateDischargeTotal();
  document.getElementById("dischargeModal").classList.add("active");
}

function closeDischargeModal() {
  document.getElementById("dischargeModal").classList.remove("active");
}

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(amount);
}

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function updateDischargeTotal() {
  const currentBill = Number(document.getElementById("dischargeCurrentBill").textContent.replace(/[^0-9.]/g, "")) || 0;
  const pharmacyCost = Number(document.getElementById("dischargePharmacyCost").value) || 0;
  document.getElementById("dischargeFinalBill").textContent = formatCurrency(currentBill + pharmacyCost);
}

async function handleDischargeSubmit(event) {
  event.preventDefault();
  const encounterId = document.getElementById("dischargeEncounterId").value;
  const pharmacyCost = Number(document.getElementById("dischargePharmacyCost").value);
  const alertBox = document.getElementById("dischargeAlert");
  const submitButton = document.getElementById("dischargeSubmit");
  if (!Number.isFinite(pharmacyCost) || pharmacyCost < 0) {
    alertBox.className = "validation-alert error";
    alertBox.style.display = "block";
    alertBox.textContent = "Enter a valid non-negative pharmacy amount.";
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Finalizing discharge...";
  alertBox.style.display = "none";
  try {
    const res = await fetch(`/api/encounters/${encodeURIComponent(encounterId)}/discharge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pharmacy_cost: pharmacyCost })
    });
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || "Discharge failed.");
    await Promise.all([loadActiveAdmissions(), loadExecutiveKPIs(), loadAnalyticsCharts()]);
    alertBox.className = "validation-alert success";
    alertBox.style.display = "block";
    alertBox.textContent = json.message;
  } catch (error) {
    alertBox.className = "validation-alert error";
    alertBox.style.display = "block";
    alertBox.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Confirm discharge";
  }
}

async function logoutAdmin() {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.assign("/auth");
}

function handlePatientSearch(event) {
  loadPatients(patientSearchUrl());
}

function filterPatients() {
  loadPatients(patientSearchUrl());
}

// ==========================================
// FULL EHR MODAL
// ==========================================
async function openEhrModal(patientId) {
  activePatientId = patientId;
  const modal = document.getElementById("ehrModal");
  const body = document.getElementById("ehrModalBody");
  body.innerHTML = "<div style='color: var(--text-muted);'>Loading comprehensive EHR from MongoDB...</div>";
  modal.classList.add("active");

  try {
    const res = await fetch(`/api/patients/${patientId}`);
    const json = await res.json();
    if (json.success && json.data) {
      const p = json.data.patient;
      const encounters = json.data.encounters || [];
      const appointments = json.data.appointments || [];

      let html = `
        <div class="chart-header">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2>${p.name} <span style="font-size: 1rem; color: var(--accent-cyan); font-family: monospace;">(${p.patient_id})</span></h2>
            <span class="bg-pill red" style="font-size: 1rem; padding: 0.3rem 0.8rem;">${p.blood_group}</span>
          </div>
          <div style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.4rem;">
            ${p.gender} • Registered: ${new Date(p.registered_at?.$date || p.registered_at).toLocaleDateString()}
          </div>
          <div style="margin-top: 0.8rem; font-size: 0.88rem; display: flex; gap: 1.5rem; flex-wrap: wrap;">
            <div><strong>Contact:</strong> ${p.contact?.phone} | ${p.contact?.email}</div>
            <div><strong>Insurance:</strong> ${p.insurance?.provider || 'Self-pay'} (${p.insurance?.policy_number || 'N/A'})</div>
          </div>
          <div class="chart-actions">
            <button class="btn btn-primary btn-sm" onclick="openAppointmentModal('${p.patient_id}')">Schedule follow-up</button>
            <button class="btn btn-outline btn-sm" onclick="openPatientEditModal('${p.patient_id}')">Edit demographics</button>
            <button class="btn btn-danger btn-sm" onclick="requestPatientDelete('${p.patient_id}')">Remove patient</button>
          </div>
        </div>

        <div class="section-heading chart-section-heading"><div><h3>Clinical history</h3><p>${encounters.length} recorded encounters</p></div></div>
      `;

      if (encounters.length === 0) {
        html += "<p style='color: var(--text-muted);'>No past encounters logged.</p>";
      } else {
        encounters.forEach(enc => {
          const admDate = enc.admission_date ? new Date(enc.admission_date.$date || enc.admission_date).toLocaleDateString() : "N/A";
          const isActive = ["Admitted", "Under_Observation"].includes(enc.status);
          const statusBadge = isActive ? "color: var(--accent-amber);" : "color: var(--accent-emerald);";
          const latestVital = enc.vitals_log?.[enc.vitals_log.length - 1];

          html += `
            <article class="encounter-card">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                <div>
                  <strong style="color: var(--accent-cyan);">${enc.encounter_id}</strong> - ${enc.department} (${enc.type})
                </div>
                <span style="font-weight: 600; font-size: 0.85rem; ${statusBadge}">${enc.status}</span>
              </div>
              <div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
                <strong>${admDate} · Diagnosis:</strong> ${enc.primary_diagnosis || "Not recorded"}
              </div>
              ${latestVital ? `<div class="chart-vitals"><strong>Latest vitals</strong><span>HR ${latestVital.heart_rate || "—"} bpm</span><span>SpO₂ ${latestVital.spo2 || "—"}%</span><span>Temp ${latestVital.temperature_f || "—"}°F</span></div>` : ""}

              <div class="chart-record-list"><strong>Prescriptions (${enc.prescriptions?.length || 0})</strong>${(enc.prescriptions || []).map(rx => `<div>${rx.medication} · ${rx.dosage} · ${rx.frequency} · ${rx.duration_days} days</div>`).join("") || `<span class="text-muted">None recorded</span>`}</div>
              <div class="chart-record-list"><strong>Visit notes (${enc.clinical_notes?.length || 0})</strong>${(enc.clinical_notes || []).map(note => `<div>${note.note}<small>${note.author || "Clinician"} · ${new Date(note.created_at?.$date || note.created_at).toLocaleString()}</small></div>`).join("") || `<span class="text-muted">None recorded</span>`}</div>

              <div class="encounter-footer"><span>Bill ₹${enc.billing?.total_amount?.toLocaleString('en-IN') || "0"}</span>${isActive ? `<button class="btn btn-outline btn-sm" onclick="openVisitModal('${enc.encounter_id}')">Document care</button>` : ""}</div>
            </article>
          `;
        });
      }

      html += `<div class="section-heading chart-section-heading"><div><h3>Follow-up appointments</h3><p>${appointments.length} appointments on file</p></div></div>`;
      if (appointments.length) {
        html += appointments.map(appointment => `<div class="chart-appointment"><strong>${new Date(appointment.appointment_time?.$date || appointment.appointment_time).toLocaleString()}</strong><span>${appointment.reason || "Follow-up"}</span><span>${appointment.status}</span></div>`).join("");
      } else {
        html += `<p class="empty-state">No appointments on file.</p>`;
      }

      body.innerHTML = html;
    }
  } catch (e) {
    body.innerHTML = `<div style='color: var(--accent-rose);'>Failed to load EHR details: ${e.message}</div>`;
  }
}

function closeEhrModal() {
  document.getElementById("ehrModal").classList.remove("active");
}

function openVisitModal(encounterId) {
  document.getElementById("visitEncounterId").value = encounterId;
  document.getElementById("visitEncounterLabel").textContent = `Encounter ${encounterId}`;
  document.getElementById("visitActionForm").reset();
  document.getElementById("visitActionAlert").style.display = "none";
  switchVisitAction();
  document.getElementById("visitModal").classList.add("active");
}

function closeVisitModal() {
  document.getElementById("visitModal").classList.remove("active");
}

function switchVisitAction() {
  const action = document.getElementById("visitActionType").value;
  document.getElementById("visitNoteFields").hidden = action !== "note";
  document.getElementById("visitVitalsFields").hidden = action !== "vitals";
  document.getElementById("visitPrescriptionFields").hidden = action !== "prescription";
  const labels = { note: "Save visit note", vitals: "Save vitals", prescription: "Add prescription" };
  document.getElementById("visitActionSubmit").textContent = labels[action];
}

async function handleVisitAction(event) {
  event.preventDefault();
  const action = document.getElementById("visitActionType").value;
  const encounterId = document.getElementById("visitEncounterId").value;
  const alertBox = document.getElementById("visitActionAlert");
  let endpoint = "";
  let payload = {};

  if (action === "note") {
    endpoint = "notes";
    payload.note = document.getElementById("visitNote").value.trim();
    if (!payload.note) return showInlineError(alertBox, "Write a visit note before saving.");
  } else if (action === "vitals") {
    endpoint = "vitals";
    const heartRate = document.getElementById("visitHeartRate").value;
    const spo2 = document.getElementById("visitSpo2").value;
    const temperature = document.getElementById("visitTemperature").value;
    if (!heartRate) return showInlineError(alertBox, "Heart rate is required to record a vital reading.");
    payload = { heart_rate: Number(heartRate) };
    if (spo2) payload.spo2 = Number(spo2);
    if (temperature) payload.temperature_f = Number(temperature);
  } else {
    endpoint = "prescriptions";
    payload = {
      medication: document.getElementById("visitMedication").value.trim(),
      dosage: document.getElementById("visitDosage").value.trim(),
      frequency: document.getElementById("visitFrequency").value.trim(),
      duration_days: Number(document.getElementById("visitDuration").value)
    };
    if (!payload.medication || !payload.dosage || !payload.frequency || payload.duration_days < 1) {
      return showInlineError(alertBox, "Enter medication, dosage, frequency, and a duration of at least one day.");
    }
  }

  const submit = document.getElementById("visitActionSubmit");
  submit.disabled = true;
  alertBox.style.display = "none";
  try {
    const response = await fetch(`/api/encounters/${encodeURIComponent(encounterId)}/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error(result.error || "Could not save this chart entry.");
    closeVisitModal();
    await Promise.all([openEhrModal(activePatientId), loadActiveAdmissions()]);
  } catch (error) {
    showInlineError(alertBox, error.message);
  } finally {
    submit.disabled = false;
  }
}

function showInlineError(element, message) {
  element.className = "validation-alert error";
  element.style.display = "block";
  element.textContent = message;
}

async function openAppointmentModal(patientId = activePatientId) {
  appointmentFromChart = Boolean(patientId);
  document.getElementById("appointmentForm").reset();
  document.getElementById("appointmentPatientId").value = patientId || "";
  document.getElementById("appointmentPatientLabel").textContent = patientId ? `Patient ${patientId}` : "Select a patient for this appointment";
  document.getElementById("appointmentPatientSelectRow").hidden = Boolean(patientId);
  document.getElementById("appointmentAlert").style.display = "none";
  const modal = document.getElementById("appointmentModal");
  modal.classList.add("active");
  try {
    const requests = [fetch("/api/doctors")];
    if (!patientId) requests.push(fetch("/api/patients"));
    const responses = await Promise.all(requests);
    const results = await Promise.all(responses.map(response => response.json()));
    if (responses.some(response => !response.ok) || results.some(result => !result.success)) {
      throw new Error("Could not load the patient and clinician lists.");
    }

    const select = document.getElementById("appointmentDoctor");
    select.replaceChildren();
    results[0].data.forEach(doctor => {
      const option = document.createElement("option");
      option.value = doctor.doctor_id;
      option.textContent = `${doctor.name} · ${doctor.department}`;
      select.appendChild(option);
    });
    if (!patientId) {
      const patientSelect = document.getElementById("appointmentPatientSelect");
      patientSelect.replaceChildren();
      results[1].data.filter(patient => patient.status === "Active").forEach(patient => {
        const option = document.createElement("option");
        option.value = patient.patient_id;
        option.textContent = `${patient.name} (${patient.patient_id})`;
        patientSelect.appendChild(option);
      });
      if (!patientSelect.options.length) throw new Error("Register an active patient before scheduling a visit.");
    }
    const defaultTime = new Date();
    defaultTime.setHours(defaultTime.getHours() + 1, 0, 0, 0);
    document.getElementById("appointmentTime").value = new Date(defaultTime - defaultTime.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  } catch (error) {
    showInlineError(document.getElementById("appointmentAlert"), error.message);
  }
}

function closeAppointmentModal() {
  document.getElementById("appointmentModal").classList.remove("active");
}

async function handleAppointmentSubmit(event) {
  event.preventDefault();
  const alertBox = document.getElementById("appointmentAlert");
  const submit = document.getElementById("appointmentSubmit");
  const payload = {
    patient_id: appointmentFromChart
      ? document.getElementById("appointmentPatientId").value
      : document.getElementById("appointmentPatientSelect").value,
    doctor_id: document.getElementById("appointmentDoctor").value,
    appointment_time: document.getElementById("appointmentTime").value,
    reason: document.getElementById("appointmentReason").value.trim()
  };
  if (!payload.patient_id) return showInlineError(alertBox, "Select a patient before saving the appointment.");
  submit.disabled = true;
  alertBox.style.display = "none";
  try {
    const response = await fetch("/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error(result.error || "Could not schedule follow-up.");
    closeAppointmentModal();
    document.getElementById("appointmentForm").reset();
    await Promise.all([loadAppointments(), loadExecutiveKPIs()]);
    if (appointmentFromChart) await openEhrModal(payload.patient_id);
  } catch (error) {
    showInlineError(alertBox, error.message);
  } finally {
    submit.disabled = false;
  }
}

async function openRegisterModal() {
  const modal = document.getElementById("registerModal");
  const alertBox = document.getElementById("registerModalAlert");
  if (alertBox) alertBox.style.display = "none";
  modal.classList.add("active");

  try {
    const res = await fetch("/api/patients/next-id");
    const json = await res.json();
    if (json.success && json.next_id) {
      document.getElementById("regId").value = json.next_id;
    }
  } catch (e) {
    console.error("Could not fetch next patient ID", e);
  }
}

function closeRegisterModal() {
  document.getElementById("registerModal").classList.remove("active");
  const alertBox = document.getElementById("registerModalAlert");
  if (alertBox) alertBox.style.display = "none";
}

async function openPatientEditModal(patientId) {
  const modal = document.getElementById("editPatientModal");
  const alertBox = document.getElementById("editPatientAlert");
  alertBox.style.display = "none";
  document.getElementById("editPatientId").value = patientId;
  modal.classList.add("active");

  try {
    const res = await fetch(`/api/patients/${encodeURIComponent(patientId)}`);
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || "Patient record could not be loaded.");
    const patient = json.data.patient;
    document.getElementById("editPatientName").value = patient.name || "";
    document.getElementById("editPatientDob").value = new Date(patient.dob?.$date || patient.dob).toISOString().slice(0, 10);
    document.getElementById("editPatientGender").value = patient.gender || "Other";
    document.getElementById("editPatientBloodGroup").value = patient.blood_group || "O+";
    document.getElementById("editPatientPhone").value = patient.contact?.phone || "";
    document.getElementById("editPatientEmail").value = patient.contact?.email || "";
    document.getElementById("editPatientConditions").value = (patient.medical_profile?.chronic_conditions || []).join(", ");
  } catch (error) {
    alertBox.className = "validation-alert error";
    alertBox.style.display = "block";
    alertBox.textContent = error.message;
  }
}

function closePatientEditModal() {
  document.getElementById("editPatientModal").classList.remove("active");
}

async function openAdmissionModal() {
  const modal = document.getElementById("admissionModal");
  const alertBox = document.getElementById("admissionAlert");
  alertBox.style.display = "none";
  modal.classList.add("active");
  try {
    const [patientsResponse, doctorsResponse, idResponse] = await Promise.all([
      fetch("/api/patients"),
      fetch("/api/doctors"),
      fetch("/api/encounters/next-id")
    ]);
    const [patientsJson, doctorsJson, idJson] = await Promise.all([
      patientsResponse.json(), doctorsResponse.json(), idResponse.json()
    ]);
    if (!patientsResponse.ok || !patientsJson.success || !doctorsResponse.ok || !doctorsJson.success || !idJson.success) {
      throw new Error("Could not load patients, doctors, or the next encounter ID.");
    }

    const patientSelect = document.getElementById("admissionPatient");
    patientSelect.replaceChildren();
    patientsJson.data.filter(patient => patient.status !== "Inactive" && patient.status !== "Deceased").forEach(patient => {
      const option = document.createElement("option");
      option.value = patient.patient_id;
      option.textContent = `${patient.name} (${patient.patient_id})`;
      patientSelect.appendChild(option);
    });

    const doctorSelect = document.getElementById("admissionDoctor");
    doctorSelect.replaceChildren();
    doctorsJson.data.forEach(doctor => {
      const option = document.createElement("option");
      option.value = doctor.doctor_id;
      option.textContent = `${doctor.name} · ${doctor.department}`;
      option.dataset.department = doctor.department;
      doctorSelect.appendChild(option);
    });
    document.getElementById("admissionEncounterId").value = idJson.next_id;
    if (!patientSelect.options.length || !doctorSelect.options.length) {
      throw new Error("An active patient and doctor are required to create an admission.");
    }
  } catch (error) {
    alertBox.className = "validation-alert error";
    alertBox.style.display = "block";
    alertBox.textContent = error.message;
  }
}

function closeAdmissionModal() {
  document.getElementById("admissionModal").classList.remove("active");
}

async function handleAdmissionSubmit(event) {
  event.preventDefault();
  const alertBox = document.getElementById("admissionAlert");
  const doctorOption = document.getElementById("admissionDoctor").selectedOptions[0];
  const payload = {
    encounter_id: document.getElementById("admissionEncounterId").value,
    patient_id: document.getElementById("admissionPatient").value,
    doctor_id: doctorOption.value,
    department: doctorOption.dataset.department,
    type: document.getElementById("admissionType").value,
    status: "Admitted",
    primary_diagnosis: document.getElementById("admissionDiagnosis").value.trim()
  };
  alertBox.className = "validation-alert";
  alertBox.style.display = "block";
  alertBox.textContent = "Creating admission...";
  try {
    const res = await fetch("/api/encounters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || "Admission could not be created.");
    closeAdmissionModal();
    document.getElementById("admissionForm").reset();
    await Promise.all([loadActiveAdmissions(), loadExecutiveKPIs(), loadAnalyticsCharts()]);
    alert(json.message);
  } catch (error) {
    alertBox.className = "validation-alert error";
    alertBox.textContent = error.message;
  }
}

async function handlePatientUpdate(event) {
  event.preventDefault();
  const alertBox = document.getElementById("editPatientAlert");
  const patientId = document.getElementById("editPatientId").value;
  const payload = {
    name: document.getElementById("editPatientName").value.trim(),
    dob: document.getElementById("editPatientDob").value,
    gender: document.getElementById("editPatientGender").value,
    blood_group: document.getElementById("editPatientBloodGroup").value,
    phone: document.getElementById("editPatientPhone").value.trim(),
    email: document.getElementById("editPatientEmail").value.trim(),
    chronic_conditions: document.getElementById("editPatientConditions").value.split(",").map(value => value.trim()).filter(Boolean)
  };
  alertBox.className = "validation-alert";
  alertBox.style.display = "block";
  alertBox.textContent = "Saving changes...";

  try {
    const res = await fetch(`/api/patients/${encodeURIComponent(patientId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || "Patient update failed.");
    closePatientEditModal();
    await loadPatients();
    await fetchSystemHealth();
    await openEhrModal(patientId);
  } catch (error) {
    alertBox.className = "validation-alert error";
    alertBox.textContent = error.message;
  }
}

function requestPatientDelete(patientId) {
  pendingDeletePatientId = patientId;
  document.getElementById("deletePatientMessage").textContent = `${patientId} can only be removed if no encounters or appointments are linked.`;
  document.getElementById("deletePatientAlert").style.display = "none";
  document.getElementById("deletePatientModal").classList.add("active");
}

function closeDeletePatientModal() {
  document.getElementById("deletePatientModal").classList.remove("active");
}

async function deletePatient() {
  const alertBox = document.getElementById("deletePatientAlert");
  try {
    const res = await fetch(`/api/patients/${encodeURIComponent(pendingDeletePatientId)}`, { method: "DELETE" });
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || "Patient deletion failed.");
    closeDeletePatientModal();
    closeEhrModal();
    await loadPatients();
    await fetchSystemHealth();
    await loadExecutiveKPIs();
  } catch (error) {
    showInlineError(alertBox, error.message);
  }
}

// ==========================================
// REGISTER PATIENT (WITH INLINE $jsonSchema FEEDBACK)
// ==========================================
async function handlePatientSubmit(e) {
  e.preventDefault();
  const alertBox = document.getElementById("registerModalAlert");
  const patientId = document.getElementById("regId").value.trim();
  const name = document.getElementById("regName").value.trim();
  const dob = document.getElementById("regDob").value;
  const gender = document.getElementById("regGender").value;
  const bloodGroup = document.getElementById("regBloodGroup").value;
  const phone = document.getElementById("regPhone").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const conditionsStr = document.getElementById("regConditions").value.trim();
  const conditions = conditionsStr ? conditionsStr.split(",").map(c => c.trim()) : [];

  const payload = {
    patient_id: patientId,
    name: name,
    dob: dob,
    gender: gender,
    blood_group: bloodGroup,
    contact: {
      phone: phone,
      email: email,
      address: { city: "New Delhi", state: "Delhi" }
    },
    medical_profile: {
      chronic_conditions: conditions,
      allergies: []
    },
    status: "Active"
  };

  alertBox.className = "validation-alert";
  alertBox.style.display = "block";
  alertBox.textContent = "Validating with MongoDB $jsonSchema engine...";

  try {
    const res = await fetch("/api/patients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (res.ok && json.success) {
      alertBox.className = "validation-alert success";
      alertBox.innerHTML = `<strong>✓ SUCCESS:</strong> ${json.message || "Patient registered successfully in MongoDB!"}`;
      loadPatients();
      fetchSystemHealth();
      loadExecutiveKPIs();
      setTimeout(() => {
        closeRegisterModal();
        document.getElementById("newPatientForm").reset();
      }, 1400);
    } else {
      alertBox.className = "validation-alert error";
      alertBox.innerHTML = `<strong>✗ VALIDATION REJECTED:</strong><br>${json.error || "Document failed MongoDB $jsonSchema constraints."}`;
    }
  } catch (err) {
    alertBox.className = "validation-alert error";
    alertBox.textContent = `Error: ${err.message}`;
  }
}

// ==========================================
// LIVE QUERY CONSOLE (TAB 3)
// ==========================================
function handleQuerySelect(queryKey) {
  const snippet = QUERY_SNIPPETS[queryKey];
  if (snippet) {
    document.getElementById("queryCodeDisplay").textContent = snippet.code;
    document.getElementById("queryOutputDisplay").textContent = "// Click Execute Query to inspect real-time MongoDB response";
  }
}

async function executeSelectedQuery() {
  const queryKey = document.getElementById("querySelector").value;
  const snippet = QUERY_SNIPPETS[queryKey];
  const outputElem = document.getElementById("queryOutputDisplay");
  if (!snippet) return;

  outputElem.textContent = "Executing query on MongoDB server...";
  const startTime = performance.now();

  try {
    const res = await fetch(snippet.endpoint);
    const json = await res.json();
    const duration = (performance.now() - startTime).toFixed(1);

    outputElem.textContent = `// Execution Time: ${duration} ms\n// Status: 200 OK\n\n` + JSON.stringify(json, null, 2);
  } catch (err) {
    outputElem.textContent = `// Query Execution Failed: ${err.message}`;
  }
}

// ==========================================
// SCHEMA VALIDATION SANDBOX (TAB 4)
// ==========================================
function loadSandboxPreset(presetKey) {
  const preset = SANDBOX_PRESETS[presetKey];
  if (preset) {
    document.getElementById("sandboxPayload").value = JSON.stringify(preset, null, 2);
    document.getElementById("sandboxAlert").style.display = "none";
  }
}

async function testSandboxValidation() {
  const text = document.getElementById("sandboxPayload").value;
  const alertBox = document.getElementById("sandboxAlert");
  let payload;

  try {
    payload = JSON.parse(text);
  } catch (e) {
    alertBox.className = "validation-alert error";
    alertBox.textContent = "Invalid JSON syntax. Please check brackets and quotes.";
    return;
  }

  alertBox.className = "validation-alert";
  alertBox.style.display = "block";
  alertBox.textContent = "Sending document to MongoDB engine for validation...";

  try {
    const res = await fetch("/api/sandbox/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.valid) {
      alertBox.className = "validation-alert success";
      alertBox.innerHTML = `<strong>✓ VALIDATION PASSED:</strong> ${json.message}`;
    } else {
      alertBox.className = "validation-alert error";
      alertBox.innerHTML = `<strong>✗ VALIDATION REJECTED BY MONGODB:</strong><br>${json.message}<br><small style="font-family: monospace; opacity: 0.9;">${json.error}</small>`;
    }
  } catch (e) {
    alertBox.className = "validation-alert error";
    alertBox.textContent = `Error: ${e.message}`;
  }
}

function autoFixSandboxPayload() {
  const text = document.getElementById("sandboxPayload").value;
  let payload;
  try {
    payload = JSON.parse(text);
  } catch (e) {
    alert("Invalid JSON format");
    return;
  }

  const doc = payload.document || {};
  // 1. Fix blood group if invalid
  if (doc.blood_group && !["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].includes(doc.blood_group)) {
    doc.blood_group = "O+";
  }
  // 2. Fix phone if invalid
  if (doc.contact && doc.contact.phone && !/^\+?[0-9\s\-()]{7,20}$/.test(doc.contact.phone)) {
    doc.contact.phone = "+91-9876543210";
  }
  // 3. Fix doctor fee if < 100
  if (typeof doc.consultation_fee === "number" && doc.consultation_fee < 100) {
    doc.consultation_fee = 1200.0;
  }
  // 4. Fix patient_id if not matching PAT-
  if (doc.patient_id && !doc.patient_id.startsWith("PAT-")) {
    doc.patient_id = `PAT-${doc.patient_id.replace(/\D/g, '') || '9501'}`;
  }

  payload.document = doc;
  document.getElementById("sandboxPayload").value = JSON.stringify(payload, null, 2);
  // Auto-run validation
  testSandboxValidation();
}


