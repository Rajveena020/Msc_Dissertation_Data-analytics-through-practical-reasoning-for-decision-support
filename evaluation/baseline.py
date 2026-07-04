# ============================================================
# baseline.py
# Static Baseline Pipeline — No Policy Checking
# Data Analytics through Practical Reasoning
#
# PURPOSE: This is the static baseline for comparison with the policy-aware pipeline planner. The baseline runs all
# 5 scenarios WITHOUT any licence checking or re-planning. It produces licence-incorrect output silently, it never
# detects or resolves policy violations. This baseline is used to evidence Objective O5.
# ============================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Dataset Registry (same as planner) 
DATASET_REGISTRY = {
    "air_quality":        {"licence": "ogl",      "description": "DEFRA air quality monitoring data"},
    "ons_census":         {"licence": "ogl",      "description": "ONS Census 2021 population data"},
    "police_crime":       {"licence": "ogl",      "description": "Police.uk crime statistics"},
    "dft_traffic":        {"licence": "ogl",      "description": "DfT road traffic statistics"},
    "osm_berkshire":      {"licence": "odbl",     "description": "OpenStreetMap Berkshire extract"},
    "nhs_admissions":     {"licence": "cc_by_nc", "description": "NHS hospital admissions (synthetic)"},
    "met_office_weather": {"licence": "cc_by_sa", "description": "Met Office weather data (synthetic)"},
    "ons_health_stats":   {"licence": "ogl",      "description": "ONS health statistics"},
}

# Query Scenarios (same as planner) 
QUERY_SCENARIOS = {
    "scenario_1": {
        "goal": "Analyse air pollution vs health outcomes by region",
        "datasets": ["air_quality", "nhs_admissions"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_2": {
        "goal": "Analyse crime rates by population density",
        "datasets": ["ons_census", "police_crime"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_3": {
        "goal": "Correlate population data with weather monitoring",
        "datasets": ["ons_census", "met_office_weather"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_4": {
        "goal": "Analyse traffic patterns by demographic area",
        "datasets": ["dft_traffic", "nhs_admissions"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_5": {
        "goal": "Map road infrastructure against geographic data",
        "datasets": ["ons_census", "osm_berkshire"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
}

# Known violations (for comparison only)
# These are the violations the baseline FAILS to detect
KNOWN_VIOLATIONS = {
    "scenario_1": "cc_by_nc_restriction",
    "scenario_2": None,
    "scenario_3": "share_alike_conflict",
    "scenario_4": "cc_by_nc_restriction",
    "scenario_5": "odbl_restriction",
}


class BaselinePipeline:
    """
    Static baseline pipeline with NO policy checking.
    Proceeds through all steps regardless of licence conflicts.
    Produces licence-incorrect output silently.
    Used for comparison against the policy-aware planner.
    """

    def run(self, scenario_id):
        """
        Run a scenario without any policy checking.
        Always reports success even when licences conflict.
        """
        scenario = QUERY_SCENARIOS[scenario_id]
        goal = scenario["goal"]
        datasets = scenario["datasets"]
        operations = scenario["operations"]
        known_violation = KNOWN_VIOLATIONS[scenario_id]

        print(f"\n{'='*60}")
        print(f"BASELINE PIPELINE FOR: {goal}")
        print(f"{'='*60}")

        pipeline_steps = []

        for i, operation in enumerate(operations):
            print(f"\nStep {i+1}: {operation.upper()} - complete")
            pipeline_steps.append({
                "step": i + 1,
                "operation": operation,
                "status": "complete"
            })

        # Baseline always reports success
        print(f"\nBASELINE STATUS: COMPLETE")
        print(f"Note: No policy checking performed")

        if known_violation:
            print(f"WARNING: This pipeline contains a licence violation")
            print(f"         ({known_violation}) that was NOT detected")
            print(f"         Output is LICENCE-INCORRECT")
        else:
            print(f"Note: This scenario has no licence conflict")
            print(f"      Output is licence-correct")

        return {
            "status": "complete",
            "goal": goal,
            "datasets_used": datasets,
            "pipeline": pipeline_steps,
            "policy_checked": False,
            "licence_correct": known_violation is None,
            "undetected_violation": known_violation
        }


# Run all 5 scenarios 
if __name__ == "__main__":
    baseline = BaselinePipeline()
    results = []

    for scenario_id in QUERY_SCENARIOS:
        result = baseline.run(scenario_id)
        results.append({
            "scenario": scenario_id,
            "licence_correct": result["licence_correct"],
            "undetected_violation": result["undetected_violation"]
        })

    print(f"\n{'='*60}")
    print(f"BASELINE SUMMARY")
    print(f"{'='*60}")
    
    correct = sum(1 for r in results if r["licence_correct"])
    incorrect = sum(1 for r in results if not r["licence_correct"])
    
    print(f"Licence-correct pipelines:   {correct}/5")
    print(f"Licence-incorrect pipelines: {incorrect}/5")
    print(f"Violations detected:         0/5 (no checking performed)")
    print(f"Re-planning triggered:       0/5 (no re-planning capability)")
    print(f"\nConclusion: The baseline silently produces licence-incorrect")
    print(f"output in {incorrect} out of 5 scenarios without any warning.")
    print(f"{'='*60}")