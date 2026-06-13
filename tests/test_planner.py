# ============================================================
# test_planner.py
# Integration Tests for Pipeline Planner
# ============================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.planner import PipelinePlanner

planner = PipelinePlanner()

def test_scenario_1_replanning():
    """OGL + CC-BY-NC - violation expected, re-plan expected"""
    result = planner.build_pipeline("scenario_1")
    assert result["status"] == "success"
    assert result["replanned"] == True
    assert result["violation"] is None
    print("PASS: Scenario 1 - violation detected and re-planned successfully")

def test_scenario_2_compliant():
    """OGL + OGL - no violation, no re-planning"""
    result = planner.build_pipeline("scenario_2")
    assert result["status"] == "success"
    assert result["replanned"] == False
    assert result["violation"] is None
    print("PASS: Scenario 2 - pipeline compliant, no re-planning needed")

def test_scenario_3_replanning():
    """OGL + CC-BY-SA - violation expected, re-plan expected"""
    result = planner.build_pipeline("scenario_3")
    assert result["status"] == "success"
    assert result["replanned"] == True
    print("PASS: Scenario 3 - share-alike conflict resolved by re-planner")

def test_scenario_4_replanning():
    """OGL + CC-BY-NC - violation expected, re-plan expected"""
    result = planner.build_pipeline("scenario_4")
    assert result["status"] == "success"
    assert result["replanned"] == True
    print("PASS: Scenario 4 - CC-BY-NC conflict resolved by re-planner")

def test_scenario_5_replanning():
    """OGL + ODbL - violation expected, re-plan expected"""
    result = planner.build_pipeline("scenario_5")
    assert result["status"] == "success"
    assert result["replanned"] == True
    print("PASS: Scenario 5 - ODbL conflict resolved by re-planner")

def test_end_to_end_integration():
    """Full integration test: query to compliant pipeline"""
    # Run all 5 scenarios
    results = []
    for scenario_id in ["scenario_1", "scenario_2", "scenario_3",
                        "scenario_4", "scenario_5"]:
        result = planner.build_pipeline(scenario_id)
        results.append(result)

    # All must succeed
    assert all(r["status"] == "success" for r in results)

    # Scenarios 1,3,4,5 must have triggered re-planning
    assert results[0]["replanned"] == True
    assert results[1]["replanned"] == False
    assert results[2]["replanned"] == True
    assert results[3]["replanned"] == True
    assert results[4]["replanned"] == True

    print("PASS: End-to-end integration - all 5 scenarios successful")

if __name__ == "__main__":
    print("=" * 55)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 55)
    test_scenario_1_replanning()
    test_scenario_2_compliant()
    test_scenario_3_replanning()
    test_scenario_4_replanning()
    test_scenario_5_replanning()
    test_end_to_end_integration()
    print()
    print("ALL INTEGRATION TESTS PASSED!")
    print("=" * 55)