# ============================================================
# json_checker.py
# JSON Field-Level Policy Compliance Checker (Proof of Concept) 
#
# PURPOSE:
# Extends the column-level compliance checker to JSON documents with nested field structures. Different fields (potentially nested at
# arbitrary depth) may carry different licence terms.
#
# The system reframes non-tabular compliance for JSON as field-level compliance where paths use dot notation
# (e.g. 'clinical.diagnosis_code'). This preserves the column-level architecture while extending it to hierarchical data structures.
# ============================================================

import sys
import os
import json
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.checker import PolicyChecker

# JSON Field-Level Licence Registry
# Each field path in the JSON structure carries its own licence. Field paths use dot notation to navigate nested
# objects (e.g. 'clinical.diagnosis_code' identifies the diagnosis_code field inside the clinical object).
# This is the JSON analogue of the tabular COLUMN_REGISTRY.

FIELD_REGISTRY = {
    "patient_records": {
        # Administrative fields (top-level)
        "record_id":              "ogl",
        "admission_date":         "ogl",
        "region":                 "ogl",

        # Nested hospital info
        "hospital.code":          "ogl",
        "hospital.type":          "ogl",

        # Patient demographics
        "patient.age_group":      "ogl",
        "patient.sex":            "ogl",

        # Clinical data - restricted (CC-BY-NC)
        "clinical.diagnosis_code": "cc_by_nc",
        "clinical.length_of_stay": "cc_by_nc",
        "clinical.medication":     "cc_by_nc",
        "clinical.notes":          "cc_by_nc",

        # Metadata
        "metadata.created_by":     "ogl",
        "metadata.validated_by":   "ogl",
    },

    # Second synthetic JSON dataset for combination scenarios
    "air_quality_json": {
        "measurement_id":          "ogl",
        "timestamp":               "ogl",
        "site.code":               "ogl",
        "site.region":             "ogl",
        "readings.pm10":           "ogl",
        "readings.no2":            "ogl",
        "readings.o3":             "ogl",
    },
}


class JSONFieldChecker:
    """
    JSON field-level policy compliance checker.

    Extends the column-level compliance approach to JSON documents by treating dot-notation field paths as the unit of compliance reasoning.

    Handles:
      1. Nested object structures (e.g. hospital.code)
      2. Fine-grained field-pair compliance checking
      3. Identification of maximum-compliant field subsets
      4. Preservation of hierarchical structure
    """

    def __init__(self):
        self.checker = PolicyChecker()

    def get_field_licence(self, dataset, field_path):
        """Return the licence of a specific field path."""
        return FIELD_REGISTRY.get(dataset, {}).get(field_path)

    def get_all_fields(self, dataset):
        """Return all field paths of a dataset."""
        return list(FIELD_REGISTRY.get(dataset, {}).keys())

    def load_json(self, file_path):
        """Load and return a JSON document."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def extract_field_value(self, record, field_path):
        """
        Extract a value from a nested record using dot-notation field path. e.g. 'hospital.code' navigates record['hospital']['code']
        """
        parts = field_path.split('.')
        current = record
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def check_fields(self, dataset1, fields1, dataset2, fields2):
        """
        Check whether combining specific field paths from two JSON datasets violates any licence.

        Returns:
            {
                "compliant": bool,
                "violations": list of dicts describing each violating field-pair combination,
                "compliant_pairs": list of pairs safe to combine,
                "total_pairs_checked": int
            }
        """
        violations = []
        compliant_pairs = []

        for f1 in fields1:
            l1 = self.get_field_licence(dataset1, f1)
            for f2 in fields2:
                l2 = self.get_field_licence(dataset2, f2)

                # Sanitise field names for ASP (replace dots)
                asp_name1 = f"{dataset1}_{f1.replace('.', '_')}"
                asp_name2 = f"{dataset2}_{f2.replace('.', '_')}"

                result = self.checker.check(
                    asp_name1, l1,
                    asp_name2, l2
                )

                if not result["compliant"]:
                    violations.append({
                        "field1":         f"{dataset1}.{f1}",
                        "licence1":       l1,
                        "field2":         f"{dataset2}.{f2}",
                        "licence2":       l2,
                        "violation_type": result["violation_type"]
                    })
                else:
                    compliant_pairs.append({
                        "field1":   f"{dataset1}.{f1}",
                        "field2":   f"{dataset2}.{f2}",
                        "licence1": l1,
                        "licence2": l2
                    })

        return {
            "compliant":           len(violations) == 0,
            "violations":          violations,
            "compliant_pairs":     compliant_pairs,
            "total_pairs_checked": len(fields1) * len(fields2)
        }

    def find_compliant_fields(self, dataset1, dataset2):
        """
        Identify the maximum subset of field paths from each dataset that can be safely combined without violating any licence.
        Bidirectional: tries shrinking dataset2 first, then dataset1 if that fails, and returns the direction preserving more fields.
        """
        fields1 = self.get_all_fields(dataset1)
        fields2 = self.get_all_fields(dataset2)

        # Direction A: shrink dataset2, keep dataset1 whole.
        safe_A_d1, safe_A_d2, excluded_A_d2 = self._shrink_fields(
            dataset1, fields1, dataset2, fields2, shrink_which=2
        )

        # Direction B: shrink dataset1, keep dataset2 whole.
        safe_B_d1, safe_B_d2, excluded_B_d1 = self._shrink_fields(
            dataset1, fields1, dataset2, fields2, shrink_which=1
        )

        total_A = len(safe_A_d1) + len(safe_A_d2)
        total_B = len(safe_B_d1) + len(safe_B_d2)

        if total_A == 0 and total_B == 0:
            return {
                "safe_fields_dataset1": [],
                "safe_fields_dataset2": [],
                "excluded_fields_dataset1": fields1,
                "excluded_fields_dataset2": fields2,
                "reduction_dataset1": f"0/{len(fields1)} fields preserved",
                "reduction_dataset2": f"0/{len(fields2)} fields preserved",
                "direction_chosen": "none",
            }

        if total_A >= total_B:
            return {
                "safe_fields_dataset1": safe_A_d1,
                "safe_fields_dataset2": safe_A_d2,
                "excluded_fields_dataset1": [],
                "excluded_fields_dataset2": excluded_A_d2,
                "reduction_dataset1": (
                    f"{len(safe_A_d1)}/{len(fields1)} fields preserved"
                ),
                "reduction_dataset2": (
                    f"{len(safe_A_d2)}/{len(fields2)} fields preserved"
                ),
                "direction_chosen": "shrink_dataset2",
            }
        else:
            return {
                "safe_fields_dataset1": safe_B_d1,
                "safe_fields_dataset2": safe_B_d2,
                "excluded_fields_dataset1": excluded_B_d1,
                "excluded_fields_dataset2": [],
                "reduction_dataset1": (
                    f"{len(safe_B_d1)}/{len(fields1)} fields preserved"
                ),
                "reduction_dataset2": (
                    f"{len(safe_B_d2)}/{len(fields2)} fields preserved"
                ),
                "direction_chosen": "shrink_dataset1",
            }

    def _shrink_fields(self, dataset1, fields1, dataset2, fields2, shrink_which):
        """
        Internal: iteratively shrink one dataset's field set until the combination is compliant, or until the shrinking set is empty.
        """
        if shrink_which == 2:
            fixed_fields = list(fields1)
            variable_fields = list(fields2)
            excluded = []
            while True:
                result = self.check_fields(
                    dataset1, fixed_fields, dataset2, variable_fields
                )
                if result["compliant"]:
                    return fixed_fields, variable_fields, excluded
                violating = set()
                for v in result["violations"]:
                    field_full = v["field2"]
                    field_name = field_full.split('.', 1)[1]
                    violating.add(field_name)
                if not violating:
                    return fixed_fields, variable_fields, excluded
                field_to_remove = list(violating)[0]
                variable_fields.remove(field_to_remove)
                excluded.append(field_to_remove)
                if not variable_fields:
                    return fixed_fields, [], excluded

        elif shrink_which == 1:
            fixed_fields = list(fields2)
            variable_fields = list(fields1)
            excluded = []
            while True:
                result = self.check_fields(
                    dataset1, variable_fields, dataset2, fixed_fields
                )
                if result["compliant"]:
                    return variable_fields, fixed_fields, excluded
                violating = set()
                for v in result["violations"]:
                    field_full = v["field1"]
                    field_name = field_full.split('.', 1)[1]
                    violating.add(field_name)
                if not violating:
                    return variable_fields, fixed_fields, excluded
                field_to_remove = list(violating)[0]
                variable_fields.remove(field_to_remove)
                excluded.append(field_to_remove)
                if not variable_fields:
                    return [], fixed_fields, excluded

        raise ValueError(f"shrink_which must be 1 or 2, got {shrink_which}")

# Demo Scenarios
if __name__ == "__main__":
    jfc = JSONFieldChecker()

    print("=" * 70)
    print("JSON FIELD-LEVEL COMPLIANCE CHECKER - PROOF OF CONCEPT")
    print("=" * 70)

    # Demo 1: Load and inspect the JSON 
    print("\n" + "-" * 70)
    print("DEMO 1: Nested JSON Structure")
    print("-" * 70)

    records = jfc.load_json("data/patient_records.json")
    first_record = records[0]

    print(f"\nLoaded {len(records)} patient records")
    print("\nExample record structure:")
    print(json.dumps(first_record, indent=2))

    print("\nField-level licence assignment:")
    for field, licence in FIELD_REGISTRY["patient_records"].items():
        print(f"  {field:35s} -> {licence}")

    # Demo 2: Field-level violation detection 
    print("\n" + "-" * 70)
    print("DEMO 2: Fine-Grained Violation Detection")
    print("-" * 70)
    print("Checking patient_records + air_quality_json combination:")
    print("(dataset-level check would exclude all patient_records)")

    result = jfc.check_fields(
        "patient_records",
        ["record_id", "region", "clinical.diagnosis_code",
         "clinical.medication"],
        "air_quality_json",
        ["measurement_id", "site.region", "readings.pm10"]
    )

    print(f"\n  Total field pairs checked: {result['total_pairs_checked']}")
    print(f"  Compliant pairs:           {len(result['compliant_pairs'])}")
    print(f"  Violating pairs:           {len(result['violations'])}")

    if result["violations"]:
        print("\n  Field-level violations:")
        for v in result["violations"][:6]:
            print(f"    {v['field1']} ({v['licence1']})"
                  f" + {v['field2']} ({v['licence2']})"
                  f" -> {v['violation_type']}")

    # Demo 3: Maximum-compliant field subset 
    print("\n" + "-" * 70)
    print("DEMO 3: Maximum-Compliant Field Subset")
    print("-" * 70)
    print("Instead of excluding patient_records entirely,identify which nested fields CAN safely be combined: ")
    subset = jfc.find_compliant_fields(
        "air_quality_json", "patient_records"
    )

    print(f"\n  air_quality_json: {subset['reduction_dataset1']}")
    print(f"  patient_records:  {subset['reduction_dataset2']}")
    print(f"\n  Preserved fields in patient_records:")
    for f in subset["safe_fields_dataset2"]:
        licence = jfc.get_field_licence("patient_records", f)
        print(f"    {f:35s} ({licence}) ✓")

    if subset["excluded_fields_dataset2"]:
        print(f"\n  Excluded fields in patient_records:")
        for f in subset["excluded_fields_dataset2"]:
            licence = jfc.get_field_licence("patient_records", f)
            print(f"    {f:35s} ({licence}) ✗")

    # Demo 4: Comparison summary 
    print("\n" + "-" * 70)
    print("DEMO 4: Comparison with Dataset-Level Approach")
    print("-" * 70)

    n_total = len(jfc.get_all_fields("patient_records"))
    n_safe = len(subset["safe_fields_dataset2"])

    print("Dataset-level checker:")
    print("  patient_records (mixed) + air_quality_json (OGL)")
    print("  -> VIOLATION -> exclude entire patient_records dataset")
    print(f"  -> Data lost: ALL {n_total} fields")

    print("\nJSON field-level checker (this work):")
    print(f"  -> VIOLATION detected on {n_total - n_safe} specific fields")
    print(f"  -> Exclude only {n_total - n_safe} clinical fields")
    print(f"  -> Data preserved: {n_safe}/{n_total} fields "
          f"({100*n_safe//n_total}%)")
    print("  -> Nested structure preserved for compliant fields")

    print("\n" + "=" * 70)
    print("CONCLUSION: Field-level checking extends the column-level compliance architecture to nested JSON structures, preserving substantially more data than dataset-level exclusion.")
    print("=" * 70)