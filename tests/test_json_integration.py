# ============================================================
# test_json_integration.py
# Integration tests for JSON field-level checker
# ============================================================

import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.json_checker import JSONFieldChecker, FIELD_REGISTRY


def test_json_checker_detects_violations():
    """
    Verifies that the JSON field-level checker detects violations at the correct field-pair granularity.
    """
    jfc = JSONFieldChecker()

    result = jfc.check_fields(
        "air_quality_json",
        ["site.region", "readings.pm10"],
        "patient_records",
        ["record_id", "clinical.diagnosis_code",
         "clinical.medication"]
    )

    # Not fully compliant — clinical fields violate
    assert result["compliant"] == False

    # All violations must involve CC-BY-NC clinical fields
    for v in result["violations"]:
        assert v["licence2"] == "cc_by_nc"
        assert "clinical" in v["field2"]

    # record_id (OGL) should never appear as violation
    for v in result["violations"]:
        assert "record_id" not in v["field2"]

    print("PASS: JSON checker identifies clinical fields as violating")


def test_json_checker_preserves_administrative_fields():
    """
    Verifies that when combining a mixed-licence JSON dataset with an OGL dataset, the administrative and demographic
    fields (OGL) are correctly preserved.
    """
    jfc = JSONFieldChecker()

    subset = jfc.find_compliant_fields(
        "air_quality_json", "patient_records"
    )

    # Administrative fields (OGL) should be preserved
    assert "record_id" in subset["safe_fields_dataset2"]
    assert "admission_date" in subset["safe_fields_dataset2"]
    assert "region" in subset["safe_fields_dataset2"]
    assert "hospital.code" in subset["safe_fields_dataset2"]

    # Clinical fields (CC-BY-NC) should be excluded
    assert "clinical.diagnosis_code" in subset["excluded_fields_dataset2"]
    assert "clinical.medication" in subset["excluded_fields_dataset2"]

    print("PASS: JSON checker preserves administrative fields, "
          "excludes clinical fields")


def test_nested_field_navigation():
    """
    Verifies that nested field paths (dot notation) are correctly navigated and their licences correctly retrieved.
    """
    jfc = JSONFieldChecker()

    # Top-level field
    assert jfc.get_field_licence(
        "patient_records", "record_id") == "ogl"

    # First-level nested
    assert jfc.get_field_licence(
        "patient_records", "hospital.code") == "ogl"

    # First-level nested, restricted
    assert jfc.get_field_licence(
        "patient_records", "clinical.diagnosis_code") == "cc_by_nc"

    print("PASS: Nested field paths correctly resolved to licences")


def test_field_value_extraction():
    """
    Verifies that values can be extracted from nested JSON records using dot notation paths.
    """
    jfc = JSONFieldChecker()

    records = jfc.load_json("data/patient_records.json")
    first = records[0]

    # Extract top-level
    assert jfc.extract_field_value(first, "record_id") is not None

    # Extract nested
    assert jfc.extract_field_value(first, "hospital.code") is not None
    assert jfc.extract_field_value(
        first, "clinical.diagnosis_code") is not None

    # Non-existent field returns None
    assert jfc.extract_field_value(first, "nonexistent.path") is None

    print("PASS: Field value extraction works for nested paths")


if __name__ == "__main__":
    print("=" * 60)
    print("JSON FIELD-LEVEL INTEGRATION TESTS")
    print("=" * 60)

    test_json_checker_detects_violations()
    test_json_checker_preserves_administrative_fields()
    test_nested_field_navigation()
    test_field_value_extraction()

    print("\nALL JSON INTEGRATION TESTS PASSED!")
    print("=" * 60)