"""
MongoDB $jsonSchema Collection Validation Rules
CSE494: Intelligent NoSQL Databases - Academic Task 2

This module enforces document-level constraints, data types, enum boundaries,
and regex formats directly within the MongoDB engine.
"""

PATIENT_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["patient_id", "name", "gender", "blood_group", "dob", "contact"],
        "properties": {
            "patient_id": {
                "bsonType": "string",
                "pattern": "^PAT-[0-9]+$",
                "description": "Must be string starting with PAT- followed by digits (e.g. PAT-1001)"
            },
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "maxLength": 100,
                "description": "Patient full name is required (2-100 characters)"
            },
            "gender": {
                "enum": ["Male", "Female", "Other"],
                "description": "Gender must be one of: Male, Female, Other"
            },
            "blood_group": {
                "enum": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                "description": "Must be a valid ABO/Rh blood group"
            },
            "dob": {
                "bsonType": "date",
                "description": "Date of birth must be a BSON Date"
            },
            "contact": {
                "bsonType": "object",
                "required": ["phone", "email"],
                "properties": {
                    "phone": {
                        "bsonType": "string",
                        "pattern": "^\\+?[0-9\\s\\-\\(\\)]{7,20}$",
                        "description": "Valid phone number with 7-20 digits"
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$",
                        "description": "Valid email address format"
                    },
                    "emergency_contact": {
                        "bsonType": "string"
                    },
                    "address": {
                        "bsonType": "object",
                        "properties": {
                            "street": {"bsonType": "string"},
                            "city": {"bsonType": "string"},
                            "state": {"bsonType": "string"},
                            "pincode": {"bsonType": "string"}
                        }
                    }
                }
            },
            "medical_profile": {
                "bsonType": "object",
                "properties": {
                    "allergies": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "chronic_conditions": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "blood_pressure_baseline": {"bsonType": "string"}
                }
            },
            "insurance": {
                "bsonType": "object",
                "properties": {
                    "provider": {"bsonType": "string"},
                    "policy_number": {"bsonType": "string"},
                    "coverage_limit": {
                        "bsonType": ["int", "long", "double", "decimal"],
                        "minimum": 0
                    },
                    "valid_until": {"bsonType": "date"}
                }
            },
            "status": {
                "enum": ["Active", "Inactive", "Deceased"]
            },
            "registered_at": {
                "bsonType": "date"
            }
        }
    }
}

DOCTOR_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["doctor_id", "name", "specialization", "department", "consultation_fee"],
        "properties": {
            "doctor_id": {
                "bsonType": "string",
                "pattern": "^DOC-[0-9]{3,}$",
                "description": "Must be string starting with DOC- followed by at least 3 digits"
            },
            "name": {
                "bsonType": "string",
                "minLength": 3
            },
            "specialization": {
                "bsonType": "string"
            },
            "department": {
                "enum": ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Oncology", "General Medicine", "Pulmonology"]
            },
            "consultation_fee": {
                "bsonType": ["int", "long", "double", "decimal"],
                "minimum": 100,
                "description": "Consultation fee must be a positive number of at least 100"
            },
            "experience_years": {
                "bsonType": ["int", "long"],
                "minimum": 0
            },
            "active": {
                "bsonType": "bool"
            }
        }
    }
}

ENCOUNTER_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["encounter_id", "patient_id", "doctor_id", "department", "type", "admission_date", "status"],
        "properties": {
            "encounter_id": {
                "bsonType": "string",
                "pattern": "^ENC-[0-9]{4,}$"
            },
            "patient_id": {
                "bsonType": "string",
                "pattern": "^PAT-[0-9]{4,}$"
            },
            "doctor_id": {
                "bsonType": "string",
                "pattern": "^DOC-[0-9]{3,}$"
            },
            "department": {
                "bsonType": "string"
            },
            "type": {
                "enum": ["Inpatient", "Outpatient", "Emergency"],
                "description": "Type of encounter: Inpatient, Outpatient, or Emergency"
            },
            "admission_date": {
                "bsonType": "date"
            },
            "discharge_date": {
                "bsonType": ["date", "null"]
            },
            "status": {
                "enum": ["Admitted", "Discharged", "Under_Observation", "Transferred"]
            },
            "primary_diagnosis": {
                "bsonType": "string"
            },
            "vitals_log": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["timestamp", "heart_rate"],
                    "properties": {
                        "timestamp": {"bsonType": "date"},
                        "heart_rate": {
                            "bsonType": ["int", "long", "double"],
                            "minimum": 30,
                            "maximum": 240
                        },
                        "spo2": {
                            "bsonType": ["int", "long", "double"],
                            "minimum": 50,
                            "maximum": 100
                        },
                        "temperature_f": {
                            "bsonType": ["int", "long", "double"],
                            "minimum": 90,
                            "maximum": 110
                        }
                    }
                }
            },
            "billing": {
                "bsonType": "object",
                "properties": {
                    "total_amount": {
                        "bsonType": ["int", "long", "double", "decimal"],
                        "minimum": 0
                    },
                    "payment_status": {
                        "enum": ["Paid", "Pending", "Partially_Paid", "Insurance_Processing"]
                    }
                }
            }
        }
    }
}

APPOINTMENT_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["appointment_id", "patient_id", "doctor_id", "appointment_time", "status"],
        "properties": {
            "appointment_id": {
                "bsonType": "string",
                "pattern": "^APT-[0-9]{4,}$"
            },
            "patient_id": {
                "bsonType": "string"
            },
            "doctor_id": {
                "bsonType": "string"
            },
            "appointment_time": {
                "bsonType": "date"
            },
            "status": {
                "enum": ["Scheduled", "Completed", "Cancelled", "No-show"]
            }
        }
    }
}

def apply_validators(db):
    """
    Creates collections with strict JSON schema validators, or updates
    existing collections via collMod command.
    """
    schemas = {
        "patients": PATIENT_SCHEMA,
        "doctors": DOCTOR_SCHEMA,
        "encounters": ENCOUNTER_SCHEMA,
        "appointments": APPOINTMENT_SCHEMA
    }
    
    existing_collections = db.list_collection_names()
    
    for coll_name, schema in schemas.items():
        if coll_name in existing_collections:
            # Update existing collection validator
            try:
                db.command({
                    "collMod": coll_name,
                    "validator": schema,
                    "validationLevel": "strict",
                    "validationAction": "error"
                })
            except Exception as e:
                # If collection was modified or has conflicting options
                pass
        else:
            # Create fresh collection with validator
            db.create_collection(
                coll_name,
                validator=schema,
                validationLevel="strict",
                validationAction="error"
            )

def parse_validation_error(details) -> str:
    """
    Parses MongoDB WriteError schema validation details into clear, actionable human-readable messages.
    """
    if not isinstance(details, dict):
        return str(details)
    
    err_info = details.get("errInfo", {})
    sub_details = err_info.get("details", {})
    rules = sub_details.get("schemaRulesNotSatisfied", [])
    
    messages = []
    
    def walk_properties(props, parent=""):
        for prop in props:
            p_name = prop.get("propertyName", "")
            full_name = f"{parent}.{p_name}" if parent else p_name
            p_desc = prop.get("description", "")
            prop_details = prop.get("details", [])
            for d in prop_details:
                op = d.get("operatorName", "")
                val = d.get("consideredValue", "")
                spec = d.get("specifiedAs", {})
                
                if op == "enum":
                    allowed = spec.get("enum", [])
                    messages.append(f"Field '{full_name}' has invalid value '{val}'. Allowed options: {allowed}")
                elif op == "pattern":
                    pattern = spec.get("pattern", "")
                    messages.append(f"Field '{full_name}' ('{val}') does not match required format '{pattern}' ({p_desc})")
                elif op == "bsonType":
                    expected = spec.get("bsonType", "")
                    messages.append(f"Field '{full_name}' must be of type {expected}, received {d.get('consideredType')}")
                elif op == "minimum":
                    min_val = spec.get("minimum", 0)
                    messages.append(f"Field '{full_name}' value {val} must be at least {min_val}")
                elif op == "required":
                    missing = d.get("missingProperties", [])
                    messages.append(f"Missing required field(s) in '{full_name}': {', '.join(missing)}")
                elif op == "properties":
                    walk_properties(d.get("propertiesNotSatisfied", []), full_name)
            
            if "missingProperties" in prop:
                messages.append(f"Missing required field(s) in '{full_name}': {', '.join(prop.get('missingProperties', []))}")

    for rule in rules:
        if rule.get("operatorName") == "required":
            missing = rule.get("missingProperties", [])
            messages.append(f"Missing required field(s): {', '.join(missing)}")
        elif rule.get("operatorName") == "properties":
            walk_properties(rule.get("propertiesNotSatisfied", []))

    if messages:
        return "; ".join(messages)
    return details.get("errmsg", "Document failed collection $jsonSchema validation rules.")
