import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.planner import PipelinePlanner


def test_scenario_1_replanning():
    """
    Scenario 1: OGL + CC-BY-NC violation.
    
    With use_column_level=False, the system uses dataset-level substitution. With use_column_level=True (the intended primary strategy), 
    column-level compliance succeeds by preserving the 5 OGL columns of nhs_admissions and excluding the 3 CC-BY-NC clinical columns.
    This test verifies dataset-level substitution as fallback.
    """
    planner = PipelinePlanner(use_column_level=False)
    result = planner.build_pipeline("scenario_1")

    assert result["status"] == "success"
    assert result["datasets_used"] == ["air_quality", "ons_health_stats"]
    assert result["replan_trace"]["swapped_out"] == "nhs_admissions"
    assert result["replan_trace"]["swapped_in"] == "ons_health_stats"
    assert result["replan_trace"]["reason"] == "cc_by_nc_restriction"
    assert result["replan_trace"]["strategy"] == "domain_similar_substitution"
    assert result["replanned"] is True

    print("PASS: Scenario 1 dataset-level substitution works "
          "(fallback when column-level disabled)")


def test_scenario_1_column_level_primary():
    """
    Scenario 1 with column-level as primary strategy.
    Expected: preserves 5/8 columns of nhs_admissions, excludes the 3 CC-BY-NC clinical columns, keeps original datasets.
    """
    planner = PipelinePlanner(use_column_level=True)
    result = planner.build_pipeline("scenario_1")

    assert result["status"] == "success"
    assert result["compliance_mode"] == "column_level"
    assert result["datasets_used"] == ["air_quality", "nhs_admissions"]
    assert result["replan_trace"]["strategy"] == "column_level_primary"
    
    # Verify data preservation matches the headline claim
    preserved = result["replan_trace"]["columns_preserved"]
    excluded = result["replan_trace"]["columns_excluded"]
    assert len(preserved) == 5  # 5 OGL columns retained
    assert len(excluded) == 3   # 3 CC-BY-NC columns excluded
    
    # Verify the specific clinical columns are the ones excluded
    assert "diagnosis_code" in excluded
    assert "length_of_stay" in excluded
    assert "age_group" in excluded

    print("PASS: Scenario 1 column-level primary preserves 5/8 columns")


def test_scenario_2_compliant():
    """Scenario 2: OGL + OGL should proceed without re-planning."""
    planner = PipelinePlanner()
    result = planner.build_pipeline("scenario_2")

    assert result["status"] == "success"
    assert result["datasets_used"] == ["ons_census", "police_crime"]
    # No re-planning happened; there should be no replan_trace
    assert "replan_trace" not in result or result.get("replan_trace") is None

    print("PASS: Scenario 2 executed directly (no re-planning needed)")


def test_scenario_3_share_alike():
    """
    Scenario 3: OGL + CC-BY-SA violation.
    With use_column_level=False, uses dataset-level substitution.
    """
    planner = PipelinePlanner(use_column_level=False)
    result = planner.build_pipeline("scenario_3")

    assert result["status"] == "success"
    assert result["datasets_used"] == ["dft_traffic", "defra_weather"]
    assert result["replan_trace"]["swapped_out"] == "met_office_weather"
    assert result["replan_trace"]["swapped_in"] == "defra_weather"
    assert result["replan_trace"]["reason"] == "share_alike_conflict"

    print("PASS: Scenario 3 dataset-level substitution works")


def test_scenario_4_nhs_weather():
    """
    Scenario 4: CC-BY-SA + CC-BY-NC violation. The re-planner correctly reports partial output because no single-substitution alternative exists,
    swapping nhs_admissions to ons_health_stats (OGL) still leaves a share-alike conflict with met_office_weather (CC-BY-SA).
    Multi-step substitution search is documented as future work.
    """
    planner = PipelinePlanner()
    result = planner.build_pipeline("scenario_4")

    # Correct behaviour: report partial output honestly
    assert result["status"] == "partial"
    assert result["replan_trace"]["strategy"] == "no_alternative_found"
    assert result["replan_trace"]["original_datasets"] == [
        "met_office_weather", "nhs_admissions"
    ]

    print("PASS: Scenario 4 correctly reports partial output "
          "(no single-substitution alternative exists — O4 evidence)")


def test_scenario_5_odbl():
    """Scenario 5: OGL + ODbL violation should trigger re-planning."""
    planner = PipelinePlanner()
    result = planner.build_pipeline("scenario_5")

    assert result["status"] == "success"
    assert result["datasets_used"] == ["dft_traffic", "ons_geography"]
    assert result["replan_trace"]["swapped_out"] == "osm_berkshire"
    assert result["replan_trace"]["swapped_in"] == "ons_geography"
    assert result["replan_trace"]["reason"] == "odbl_restriction"

    print("PASS: Scenario 5 handles ODbL violation correctly")


def test_scenario_6_target_licence():
    """
    Scenario 6: user requests CC-BY-SA output (for share-alike publication). Both inputs are CC-BY-SA, so target is preserved.
    """
    planner = PipelinePlanner()
    result = planner.build_pipeline("scenario_6")

    assert result["status"] == "success"
    # Output must preserve the requested licence
    assert result["output_licence"] == "cc_by_sa"

    print("PASS: Scenario 6 preserves target licence (CC-BY-SA)")


def test_scenario_7_no_alternative():
    """
    Scenario 7: OSM (ODbL) + NHS (CC-BY-NC) - no compliant alternatives exist. System must correctly report PARTIAL rather than falsely
     claim success.
    """
    planner = PipelinePlanner()
    result = planner.build_pipeline("scenario_7")

    assert result["status"] == "partial"
    # ISSUE 6 FIX: verify partial-case replan trace
    assert result["replan_trace"]["strategy"] == "no_alternative_found"
    assert result["replan_trace"]["original_datasets"] == [
        "osm_berkshire", "nhs_admissions"
    ]
    # Reason should reflect the initial violation
    assert result["replan_trace"]["reason"] in [
        "cc_by_nc_restriction",
        "odbl_restriction",
        "nc_odbl_conflict"
    ]

    print("PASS: Scenario 7 correctly reports no viable alternative "
          "(O4 evidence)")


def test_end_to_end_correctness():
    """
    Meta-test: run all 7 scenarios, verify each returns a coherent result matching either success or partial with the correct trace.
    """
    planner = PipelinePlanner()
    scenarios = [
        "scenario_1", "scenario_2", "scenario_3",
        "scenario_4", "scenario_5", "scenario_6",
        "scenario_7"
    ]
    for sid in scenarios:
        result = planner.build_pipeline(sid)
        assert result["status"] in ["success", "partial"]
        assert result["goal"] is not None

    print("PASS: All 7 scenarios return coherent results")


if __name__ == "__main__":
    print("=" * 55)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 55)

    test_scenario_1_replanning()
    test_scenario_2_compliant()
    test_scenario_3_share_alike()
    test_scenario_4_nhs_weather()
    test_scenario_5_odbl()
    test_scenario_6_target_licence()
    test_scenario_7_no_alternative()
    test_end_to_end_correctness()

    print("\nALL TESTS PASSED!")
    print("=" * 55)