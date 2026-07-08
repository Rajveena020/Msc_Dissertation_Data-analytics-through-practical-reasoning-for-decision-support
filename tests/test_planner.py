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

def test_scenario_6_compatible_same_licence():
    """CC-BY-SA + CC-BY-SA - compatible, no re-planning,
       derived licence preserved as CC-BY-SA"""
    result = planner.build_pipeline("scenario_6")
    assert result["status"] == "success"
    assert result["replanned"] == False
    assert result["output_licence"] == "cc_by_sa"
    print("PASS: Scenario 6 - same-family CC-BY-SA compatible,"
          " output licence preserved (derived licence reasoning)")

def test_scenario_7_no_alternative():
    """Failure case: no compliant alternative exists (O4)"""
    result = planner.build_pipeline("scenario_7")
    assert result["status"] == "partial"
    assert result["replanned"] == True
    print("PASS: Scenario 7 - correctly reports no compliant alternative"
          " (Objective O4)")

def test_end_to_end_integration():
    """Full integration test: all scenarios behave as expected"""
    results = []
    for scenario_id in ["scenario_1", "scenario_2", "scenario_3",
                        "scenario_4", "scenario_5", "scenario_6",
                        "scenario_7"]:
        result = planner.build_pipeline(scenario_id)
        results.append(result)

    # Scenarios 1-6 must succeed
    assert results[0]["status"] == "success"  # re-planned
    assert results[1]["status"] == "success"  # compliant
    assert results[2]["status"] == "success"  # re-planned
    assert results[3]["status"] == "success"  # re-planned
    assert results[4]["status"] == "success"  # re-planned
    assert results[5]["status"] == "success"  # compatible same-family

    # Scenario 7 must correctly report partial
    assert results[6]["status"] == "partial"

    # Re-planning breakdown
    assert results[0]["replanned"] == True   # OGL + CC-BY-NC
    assert results[1]["replanned"] == False  # OGL + OGL
    assert results[2]["replanned"] == True   # OGL + CC-BY-SA
    assert results[3]["replanned"] == True   # OGL + CC-BY-NC
    assert results[4]["replanned"] == True   # OGL + ODbL
    assert results[5]["replanned"] == False  # CC-BY-SA + CC-BY-SA
    assert results[6]["replanned"] == True   # attempted re-plan

    print("PASS: End-to-end integration - all 7 scenarios behave correctly")


if __name__ == "__main__":
    print("=" * 55)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 55)
    test_scenario_1_replanning()
    test_scenario_2_compliant()
    test_scenario_3_replanning()
    test_scenario_4_replanning()
    test_scenario_5_replanning()
    test_scenario_6_compatible_same_licence()
    test_scenario_7_no_alternative()
    test_end_to_end_integration()
    print()
    print("ALL INTEGRATION TESTS PASSED!")
    print("=" * 55)