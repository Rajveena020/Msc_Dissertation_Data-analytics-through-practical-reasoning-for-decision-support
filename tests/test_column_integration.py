import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.planner import PipelinePlanner

def test_dataset_level_and_column_level_produce_different_outcomes():
    """
    Verifies that dataset-level and column-level compliance
    give different outcomes for the same scenario, and that
    column-level preserves more data.
    """
    # Dataset-level planner
    ds_planner = PipelinePlanner(use_column_level=False)
    ds_result = ds_planner.build_pipeline("scenario_1")
    
    # Column-level planner
    col_planner = PipelinePlanner(use_column_level=True)
    col_result = col_planner.build_pipeline("scenario_1")
    
    # Dataset-level triggered re-planning (excluded nhs_admissions)
    assert ds_result["replanned"] == True
    
    # Column-level found compliance without re-planning
    assert col_result["compliance_mode"] == "column_level"
    
    # Column-level preserved some nhs_admissions columns
    assert "nhs_admissions" in col_result["datasets_used"]
    
    print("PASS: Dataset-level and column-level produce"
          " different but valid outcomes")


def test_column_level_identifies_specific_violating_columns():
    """
    Verifies that the column-level checker identifies 
    exactly which columns cause a violation.
    """
    from src.column_checker import ColumnLevelChecker
    ccc = ColumnLevelChecker()
    
    result = ccc.check_columns(
        "air_quality",
        ["date", "pm10", "no2", "region"],
        "nhs_admissions", 
        ["hospital_code", "region", "diagnosis_code", "age_group"]
    )
    
    # There are violations
    assert not result["compliant"]
    
    # The violations are all against CC-BY-NC columns
    for v in result["violations"]:
        assert v["licence2"] == "cc_by_nc"
    
    # No violations involve OGL columns from nhs_admissions
    for v in result["violations"]:
        col2_name = v["column2"].split(".")[1]
        # These should NOT appear as violations
        assert col2_name != "hospital_code"
        assert col2_name != "region"
    
    print("PASS: Column-level checker identifies exactly the "
          "CC-BY-NC columns as violating")


if __name__ == "__main__":
    print("=" * 60)
    print("COLUMN-LEVEL INTEGRATION TESTS")
    print("=" * 60)
    test_dataset_level_and_column_level_produce_different_outcomes()
    test_column_level_identifies_specific_violating_columns()
    print("\nALL INTEGRATION TESTS PASSED!")