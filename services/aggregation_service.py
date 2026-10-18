"""
Aggregation Pipelines Service Layer for MediPulse EHR
CSE494: Intelligent NoSQL Databases - Academic Task 2

Implements 5 deep, clinical & operational aggregation pipelines:
1. Departmental Financial & Capacity Performance ($match, $group, $sort, $project)
2. Doctor Workload & Clinical Revenue Contribution ($lookup, $unwind, $group, $sort, $project)
3. Medication Utilization & Prescription Trends ($unwind, $group, $sort, $limit, $project)
4. Executive Multi-Faceted Operational Dashboard ($facet, $project)
5. Age-Stratified Risk & Length of Stay Distribution ($addFields, $bucket, $project)
"""

from typing import List, Dict, Any
from database.connection import get_database

class AggregationService:
    def __init__(self):
        self.db = get_database()
        self.encounters = self.db.encounters
        self.patients = self.db.patients

    # =========================================================================
    # PIPELINE 1: Departmental Financial & Operational Analytics
    # Stages: $match -> $group -> $sort -> $project
    # =========================================================================
    def get_department_financial_analytics(self) -> List[Dict[str, Any]]:
        """
        Calculates total encounters, admitted patient counts, total billing revenue,
        average patient bill, and total insurance claims per department.
        """
        pipeline = [
            {
                "$match": {
                    "billing.total_amount": {"$exists": True, "$gt": 0}
                }
            },
            {
                "$group": {
                    "_id": "$department",
                    "total_encounters": {"$sum": 1},
                    "total_revenue": {"$sum": "$billing.total_amount"},
                    "avg_revenue_per_encounter": {"$avg": "$billing.total_amount"},
                    "total_insurance_claimed": {"$sum": "$billing.insurance_claimed"},
                    "inpatient_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$type", "Inpatient"]}, 1, 0]
                        }
                    },
                    "emergency_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$type", "Emergency"]}, 1, 0]
                        }
                    }
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$project": {
                    "_id": 0,
                    "department": "$_id",
                    "total_encounters": 1,
                    "inpatient_count": 1,
                    "emergency_count": 1,
                    "total_revenue": {"$round": ["$total_revenue", 2]},
                    "avg_revenue_per_encounter": {"$round": ["$avg_revenue_per_encounter", 2]},
                    "total_insurance_claimed": {"$round": ["$total_insurance_claimed", 2]},
                    "patient_out_of_pocket": {
                        "$round": [{"$subtract": ["$total_revenue", "$total_insurance_claimed"]}, 2]
                    }
                }
            }
        ]
        return list(self.encounters.aggregate(pipeline))

    # =========================================================================
    # PIPELINE 2: Doctor Workload & Cross-Collection Revenue Analytics
    # Stages: $lookup -> $unwind -> $group -> $sort -> $project
    # =========================================================================
    def get_doctor_performance_analytics(self) -> List[Dict[str, Any]]:
        """
        Performs a $lookup join between encounters and doctors to calculate
        the clinical workload, treated unique patients, and generated hospital revenue per doctor.
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "doctors",
                    "localField": "doctor_id",
                    "foreignField": "doctor_id",
                    "as": "doctor_info"
                }
            },
            {
                "$unwind": "$doctor_info"
            },
            {
                "$group": {
                    "_id": {
                        "doctor_id": "$doctor_id",
                        "doctor_name": "$doctor_info.name",
                        "specialization": "$doctor_info.specialization",
                        "department": "$doctor_info.department"
                    },
                    "total_encounters_handled": {"$sum": 1},
                    "unique_patients_treated": {"$addToSet": "$patient_id"},
                    "total_billing_generated": {"$sum": "$billing.total_amount"},
                    "avg_encounter_billing": {"$avg": "$billing.total_amount"}
                }
            },
            {
                "$sort": {"total_billing_generated": -1}
            },
            {
                "$project": {
                    "_id": 0,
                    "doctor_id": "$_id.doctor_id",
                    "doctor_name": "$_id.doctor_name",
                    "specialization": "$_id.specialization",
                    "department": "$_id.department",
                    "total_encounters_handled": 1,
                    "unique_patients_count": {"$size": "$unique_patients_treated"},
                    "total_billing_generated": {"$round": ["$total_billing_generated", 2]},
                    "avg_encounter_billing": {"$round": ["$avg_encounter_billing", 2]}
                }
            }
        ]
        return list(self.encounters.aggregate(pipeline))

    # =========================================================================
    # PIPELINE 3: Medication Utilization & Prescription Trends
    # Stages: $unwind -> $group -> $sort -> $limit -> $project
    # =========================================================================
    def get_medication_utilization_analytics(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Unwinds the nested prescriptions array to find the most commonly prescribed
        drugs, departments using them, and average treatment duration.
        """
        pipeline = [
            {
                "$unwind": "$prescriptions"
            },
            {
                "$group": {
                    "_id": "$prescriptions.medication",
                    "prescription_count": {"$sum": 1},
                    "avg_duration_days": {"$avg": "$prescriptions.duration_days"},
                    "prescribing_departments": {"$addToSet": "$department"},
                    "distinct_patients": {"$addToSet": "$patient_id"}
                }
            },
            {
                "$sort": {"prescription_count": -1, "_id": 1}
            },
            {
                "$limit": top_n
            },
            {
                "$project": {
                    "_id": 0,
                    "medication": "$_id",
                    "prescription_count": 1,
                    "avg_duration_days": {"$round": ["$avg_duration_days", 1]},
                    "department_count": {"$size": "$prescribing_departments"},
                    "departments": "$prescribing_departments",
                    "unique_patients": {"$size": "$distinct_patients"}
                }
            }
        ]
        return list(self.encounters.aggregate(pipeline))

    # =========================================================================
    # PIPELINE 4: Multi-Faceted Hospital Executive Dashboard ($facet)
    # Stages: $facet -> multiple parallel aggregations
    # =========================================================================
    def get_executive_kpi_dashboard(self) -> Dict[str, Any]:
        """
        Executes multiple analytical sub-pipelines in parallel over the encounters collection
        using $facet to produce a single comprehensive executive KPI payload.
        """
        pipeline = [
            {
                "$facet": {
                    "encounter_type_distribution": [
                        {
                            "$group": {
                                "_id": "$type",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$project": {"_id": 0, "type": "$_id", "count": 1}}
                    ],
                    "status_overview": [
                        {
                            "$group": {
                                "_id": "$status",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$project": {"_id": 0, "status": "$_id", "count": 1}}
                    ],
                    "financial_overview": [
                        {
                            "$group": {
                                "_id": None,
                                "gross_revenue": {"$sum": "$billing.total_amount"},
                                "avg_bill": {"$avg": "$billing.total_amount"},
                                "min_bill": {"$min": "$billing.total_amount"},
                                "max_bill": {"$max": "$billing.total_amount"},
                                "total_insurance_covered": {"$sum": "$billing.insurance_claimed"}
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "gross_revenue": {"$round": ["$gross_revenue", 2]},
                                "avg_bill": {"$round": ["$avg_bill", 2]},
                                "min_bill": {"$round": ["$min_bill", 2]},
                                "max_bill": {"$round": ["$max_bill", 2]},
                                "total_insurance_covered": {"$round": ["$total_insurance_covered", 2]}
                            }
                        }
                    ],
                    "critical_vitals_count": [
                        {"$unwind": "$vitals_log"},
                        {
                            "$match": {
                                "$or": [
                                    {"vitals_log.heart_rate": {"$gte": 100}},
                                    {"vitals_log.spo2": {"$lte": 93}}
                                ]
                            }
                        },
                        {"$count": "alert_readings"}
                    ]
                }
            }
        ]
        results = list(self.encounters.aggregate(pipeline))
        return results[0] if results else {}

    # =========================================================================
    # PIPELINE 5: Age-Stratified Risk & Demographics Distribution ($bucket)
    # Stages: $addFields (calculate age from dob) -> $bucket -> $project
    # =========================================================================
    def get_patient_age_stratification(self) -> List[Dict[str, Any]]:
        """
        Calculates patient age dynamically from DOB and categorizes patients into
        demographic age buckets (Youth: 18-30, Middle: 30-50, Mature: 50-70, Senior: 70+)
        to examine chronic condition prevalence.
        """
        pipeline = [
            {
                "$addFields": {
                    "age": {
                        "$dateDiff": {
                            "startDate": "$dob",
                            "endDate": "$$NOW",
                            "unit": "year"
                        }
                    }
                }
            },
            {
                "$bucket": {
                    "groupBy": "$age",
                    "boundaries": [0, 30, 50, 70, 120],
                    "default": "Unknown",
                    "output": {
                        "count": {"$sum": 1},
                        "average_age": {"$avg": "$age"},
                        "blood_groups": {"$addToSet": "$blood_group"},
                        "total_chronic_conditions": {
                            "$sum": {"$size": {"$ifNull": ["$medical_profile.chronic_conditions", []]}}
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "age_bracket": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$_id", 0]}, "then": "18 - 29 (Young Adult)"},
                                {"case": {"$eq": ["$_id", 30]}, "then": "30 - 49 (Adult)"},
                                {"case": {"$eq": ["$_id", 50]}, "then": "50 - 69 (Mature Adult)"},
                                {"case": {"$eq": ["$_id", 70]}, "then": "70+ (Senior Citizen)"}
                            ],
                            "default": "Other"
                        }
                    },
                    "patient_count": "$count",
                    "average_age": {"$round": ["$average_age", 1]},
                    "total_chronic_conditions": 1,
                    "avg_chronic_conditions_per_patient": {
                        "$round": [
                            {"$divide": ["$total_chronic_conditions", "$count"]},
                            2
                        ]
                    }
                }
            }
        ]
        return list(self.patients.aggregate(pipeline))
