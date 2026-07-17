# ============================================================
# create_synthetic_json.py
# Creates a synthetic nested JSON dataset for JSON-level compliance checking demonstration.
#
# Structure: nested patient records where different fields
# carry different licences based on their sensitivity:
#   - Administrative fields (record_id, admission_date, region)
#     → OGL (openly shareable)
#   - Clinical fields (diagnosis, medication, notes)
#     → CC-BY-NC (non-commercial only)
#   - Metadata fields (created_by, validated_by)
#     → OGL (administrative info)
# ============================================================

import json
import os
import random
from datetime import datetime, timedelta

random.seed(42)

REGIONS = ["London", "South East", "South West",
           "East of England", "Midlands"]
HOSPITALS = ["RJ1", "RQM", "RRV", "RYJ", "RAX"]
DIAGNOSES = ["J45", "I10", "E11", "J44", "F32"]
MEDICATIONS = ["Salbutamol", "Ramipril", "Metformin",
               "Tiotropium", "Sertraline"]
STAFF = ["Dr Smith", "Dr Patel", "Dr Chen",
         "Dr Williams", "Dr Garcia"]

base_date = datetime(2025, 1, 1)


def generate_record(i):
    """Generate a synthetic nested patient record."""
    admission_date = (base_date + timedelta(days=i * 3)
                      ).strftime("%Y-%m-%d")

    return {
        "record_id":       f"REC-{1000 + i:04d}",
        "admission_date":  admission_date,
        "region":          random.choice(REGIONS),
        "hospital": {
            "code":        random.choice(HOSPITALS),
            "type":        random.choice(["NHS Trust", "Foundation"]),
        },
        "patient": {
            "age_group":   random.choice(
                ["0-17", "18-34", "35-54", "55-74", "75+"]),
            "sex":         random.choice(["M", "F"]),
        },
        "clinical": {
            "diagnosis_code":  random.choice(DIAGNOSES),
            "length_of_stay":  random.randint(1, 14),
            "medication":      random.choice(MEDICATIONS),
            "notes":           f"Patient responded well to treatment.",
        },
        "metadata": {
            "created_by":   random.choice(STAFF),
            "validated_by": random.choice(STAFF),
        }
    }


records = [generate_record(i) for i in range(50)]

output_path = os.path.join("data", "patient_records.json")
with open(output_path, "w") as f:
    json.dump(records, f, indent=2)

print(f"Created: {output_path} ({len(records)} records)")
print()
print("Field-level licence mapping (in COLUMN_REGISTRY style):")
print("  Administrative (OGL):")
print("    record_id, admission_date, region")
print("    hospital.code, hospital.type")
print("    metadata.created_by, metadata.validated_by")
print()
print("  Patient demographic (OGL):")
print("    patient.age_group, patient.sex")
print()
print("  Clinical (CC-BY-NC):")
print("    clinical.diagnosis_code")
print("    clinical.length_of_stay")
print("    clinical.medication")
print("    clinical.notes")