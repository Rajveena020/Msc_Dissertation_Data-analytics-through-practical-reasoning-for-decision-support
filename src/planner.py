# ============================================================
# planner.py
# Pipeline Planner - YAWL-grounded workflow construction
# Data Analytics through Practical Reasoning
# ============================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.checker import PolicyChecker

# Dataset Registry 
# All available datasets and their licences
# This simulates what would come from a real data catalogue

DATASET_REGISTRY = {
    "air_quality":       {"licence": "ogl",      "description": "DEFRA air quality monitoring data"},
    "ons_census":        {"licence": "ogl",       "description": "ONS Census 2021 population data"},
    "police_crime":      {"licence": "ogl",       "description": "Police.uk crime statistics"},
    "dft_traffic":       {"licence": "ogl",       "description": "DfT road traffic statistics"},
    "osm_berkshire":     {"licence": "odbl",      "description": "OpenStreetMap Berkshire extract"},
    "nhs_admissions":    {"licence": "cc_by_nc",  "description": "NHS hospital admissions (simulated)"},
    "met_office_weather":{"licence": "cc_by_sa",  "description": "Met Office weather data"},
    "ons_health_stats":  {"licence": "ogl",       "description": "ONS health statistics (OGL alternative)"},
}

# Query Scenarios 
# Each scenario defines a query goal and the datasets needed

QUERY_SCENARIOS = {
    "scenario_1": {
        "goal": "Analyse air pollution vs health outcomes",
        "datasets": ["air_quality", "nhs_admissions"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_2": {
        "goal": "Analyse crime rates by population density",
        "datasets": ["ons_census", "police_crime"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_3": {
        "goal": "Correlate energy use with weather patterns",
        "datasets": ["air_quality", "met_office_weather"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_4": {
        "goal": "Analyse traffic patterns by demographic area",
        "datasets": ["dft_traffic", "nhs_admissions"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
    "scenario_5": {
        "goal": "Map flood risk against road infrastructure",
        "datasets": ["dft_traffic", "osm_berkshire"],
        "operations": ["load", "clean", "merge", "analyse"]
    },
}

class PipelinePlanner:
    """
    Constructs policy-compliant analytics pipelines
    grounded in YAWL workflow patterns.

    YAWL patterns used:
    - Sequence: ordered pipeline steps
    - XOR-split: alternative dataset selection on violation
    - Cancellation: cancel remaining steps on re-plan trigger
    """

    def __init__(self):
        self.checker = PolicyChecker()
        self.registry = DATASET_REGISTRY

    def get_licence(self, dataset):
        if dataset in self.registry:
            return self.registry[dataset]["licence"]
        return None

    def find_alternative(self, dataset, excluded):
        """
        XOR-split pattern: find an alternative dataset with a compatible licence when violation detected.
        Returns None if no alternative found.
        """
        original_licence = self.get_licence(dataset)
        for alt_name, alt_info in self.registry.items():
            if alt_name in excluded:
                continue
            if alt_name == dataset:
                continue
            # Check if alternative has OGL licence (most compatible)
            if alt_info["licence"] == "ogl":
                return alt_name
        return None

    def build_pipeline(self, scenario_id, excluded_datasets=None):
        """
        Build a policy-compliant pipeline for a given scenario.
        Uses YAWL sequence pattern for step ordering.
        Calls checker before each merge step.
        If violation detected, triggers re-planning.

        Args:
            scenario_id: key from QUERY_SCENARIOS
            excluded_datasets: list of datasets to exclude (re-planning)

        Returns:
            dict with pipeline steps, status and re-plan info
        """
        if excluded_datasets is None:
            excluded_datasets = []

        scenario = QUERY_SCENARIOS[scenario_id]
        goal = scenario["goal"]
        datasets = scenario["datasets"]
        operations = scenario["operations"]

        print(f"\n{'='*60}")
        print(f"PLANNING PIPELINE FOR: {goal}")
        print(f"{'='*60}")

        pipeline_steps = []
        violation_info = None

        # YAWL Sequence Pattern 
        # Execute steps in order, checking policy at merge step

        for i, operation in enumerate(operations):
            step = {
                "step": i + 1,
                "operation": operation,
                "datasets": datasets,
                "status": None
            }

            # Policy check happens at the MERGE step
            if operation == "merge" and len(datasets) >= 2:
                d1 = datasets[0]
                d2 = datasets[1]

                # Skip excluded datasets
                if d1 in excluded_datasets or d2 in excluded_datasets:
                    alt = self.find_alternative(
                        d2 if d2 in excluded_datasets else d1,
                        excluded_datasets
                    )
                    if alt:
                        if d2 in excluded_datasets:
                            datasets = [d1, alt]
                        else:
                            datasets = [alt, d2]
                        d1, d2 = datasets[0], datasets[1]
                    else:
                        step["status"] = "failed"
                        step["reason"] = "No alternative dataset available"
                        pipeline_steps.append(step)
                        break

                l1 = self.get_licence(d1)
                l2 = self.get_licence(d2)

                print(f"\nStep {i+1}: {operation.upper()}")
                print(f"  Checking: {d1} ({l1}) + {d2} ({l2})")

                result = self.checker.check(d1, l1, d2, l2)

                if result["compliant"]:
                    step["status"] = "compliant"
                    step["datasets"] = [d1, d2]
                    print(f"  Status: COMPLIANT ✓")
                else:
                    step["status"] = "violation"
                    step["violation_type"] = result["violation_type"]
                    step["datasets"] = [d1, d2]
                    violation_info = result
                    print(f"  Status: VIOLATION ✗")
                    print(f"  Type: {result['violation_type']}")
                    print(f"  Explanation: {result['explanation']}")

                    # YAWL Cancellation Region 
                    # Cancel remaining steps and trigger re-plan
                    print(f"\n  Triggering re-planner...")
                    pipeline_steps.append(step)
                    return self.replan(scenario_id, d2, excluded_datasets, violation_info)
            else:
                step["status"] = "complete"
                print(f"\nStep {i+1}: {operation.upper()} - complete")

            pipeline_steps.append(step)

        # Pipeline completed successfully
        print(f"\nPIPELINE STATUS: COMPLETE ✓")
        print(f"All steps executed successfully")
        return {
            "status": "success",
            "goal": goal,
            "pipeline": pipeline_steps,
            "datasets_used": datasets,
            "replanned": len(excluded_datasets) > 0,
            "violation": None
        }

    def replan(self, scenario_id, violated_dataset, excluded_datasets, violation_info):
        """
        Re-planning: run planner again with violated constraint as new condition. Finds closest achievable alternative.
        """
        print(f"\n{'-'*60}")
        print(f"RE-PLANNING...")
        print(f"Excluding: {violated_dataset}")
        print(f"Reason: {violation_info['violation_type']}")
        print(f"{'-'*60}")

        # Add violated dataset to exclusion list
        new_excluded = excluded_datasets + [violated_dataset]

        # Find alternative dataset
        alt_dataset = self.find_alternative(violated_dataset, new_excluded)

        if alt_dataset:
            print(f"Alternative found: {alt_dataset} ({self.get_licence(alt_dataset)})")
            # Re-run planner with new excluded list
            return self.build_pipeline(scenario_id, new_excluded)
        else:
            print(f"No alternative found - closest achievable alternative:")
            print(f"Running scenario with available OGL datasets only")
            return {
                "status": "partial",
                "goal": QUERY_SCENARIOS[scenario_id]["goal"],
                "pipeline": [],
                "datasets_used": [],
                "replanned": True,
                "violation": violation_info,
                "message": "Original goal unreachable - no compliant alternative found"
            }


# Run all 5 scenarios 
if __name__ == "__main__":
    planner = PipelinePlanner()

    for scenario_id in QUERY_SCENARIOS:
        result = planner.build_pipeline(scenario_id)
        print(f"\nFINAL RESULT: {result['status'].upper()}")
        if result.get("replanned"):
            print(f"Re-planning was triggered")
        print(f"{'='*60}\n")