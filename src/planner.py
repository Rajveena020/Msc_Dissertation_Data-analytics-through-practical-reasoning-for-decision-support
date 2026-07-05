# ============================================================
# planner.py
# Pipeline Planner - YAWL-grounded workflow construction
# ============================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.checker import PolicyChecker

# Dataset Registry 
DATASET_REGISTRY = {
    "air_quality":        {"licence": "ogl",      "description": "DEFRA air quality monitoring data"},
    "ons_census":         {"licence": "ogl",      "description": "ONS Census 2021 population data"},
    "police_crime":       {"licence": "ogl",      "description": "Police.uk crime statistics"},
    "dft_traffic":        {"licence": "ogl",      "description": "DfT road traffic statistics"},
    "osm_berkshire":      {"licence": "odbl",     "description": "OpenStreetMap Berkshire extract"},
    "met_office_weather": {"licence": "cc_by_sa", "description": "Met Office weather data (synthetic)"},
    "nhs_admissions":     {"licence": "cc_by_nc", "description": "NHS hospital admissions (simulated)"},
    "met_office_scotland":{"licence": "cc_by_sa", "description": "Met Office Scotland regional data (synthetic)"},
    "ons_health_stats":   {"licence": "ogl",      "description": "ONS health statistics (OGL alternative)"},
}

# Domain similarity mapping 
# Maps each dataset to closest domain-similar alternatives
# Used by XOR-split re-planner to find best alternative
DOMAIN_ALTERNATIVES = {
    "nhs_admissions":     ["ons_health_stats", "ons_census"],
    "met_office_weather": ["air_quality", "ons_census"],
    "osm_berkshire":      ["dft_traffic", "ons_census"],
    "air_quality":        ["ons_health_stats", "ons_census"],
    "dft_traffic":        ["ons_census", "police_crime"],
    "ons_census":         ["police_crime", "dft_traffic"],
    "police_crime":       ["ons_census", "dft_traffic"],
    "ons_health_stats":   ["ons_census", "police_crime"],
    "met_office_scotland": ["met_office_weather", "ons_census"],
}
# Licence Restrictiveness Ranking 
# Used to determine the licence of the derived (output) dataset after merging. Most-restrictive-wins rule.
LICENCE_RANK = {
    "ogl":       1,   # Least restrictive
    "cc_by":     2,
    "cc_by_sa":  3,
    "odbl":      3,
    "cc_by_nc":  4,   # Most restrictive
}

# Query Scenarios 
# Updated goals to match actual dataset content
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
    "scenario_6": {
        "goal": "Combine weather monitoring across UK regions",
        "datasets": ["met_office_weather", "met_office_scotland"],
        "operations": ["load", "clean", "merge", "analyse"]
    }
}

class PipelinePlanner:
    """
    Constructs policy-compliant analytics pipelines grounded in YAWL workflow patterns.

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

    def find_alternative(self, dataset, excluded, target_licence=None):
        """
        XOR-split pattern: find the closest domain-similar alternative dataset when a violation is detected.
        If target_licence is specified, prefers alternatives with that licence. Otherwise defaults to OGL alternatives.

        Priority order:
        1. Domain-similar alternative with target licence
        2. Domain-similar alternative with OGL
        3. Any dataset with target licence
        4. Any OGL dataset (fallback)
        """
        preferred_licence = target_licence if target_licence else "ogl"

        # Try domain-similar with preferred licence first
        similar = DOMAIN_ALTERNATIVES.get(dataset, [])
        for alt in similar:
            if alt in excluded or alt == dataset:
                continue
            if self.get_licence(alt) == preferred_licence:
                return alt

        # Try any dataset with preferred licence
        for alt_name, alt_info in self.registry.items():
            if alt_name in excluded or alt_name == dataset:
                continue
            if alt_info["licence"] == preferred_licence:
                return alt_name

        # Fallback: OGL if not already tried
        if preferred_licence != "ogl":
            for alt_name, alt_info in self.registry.items():
                if alt_name in excluded or alt_name == dataset:
                    continue
                if alt_info["licence"] == "ogl":
                    return alt_name

        return None
    
    def derive_output_licence(self, d1, d2):
        """
        Determine the licence of the derived dataset after merging. Applies the most-restrictive-wins rule: the output inherits
        the more restrictive of the two input licences.

        """
        l1 = self.get_licence(d1)
        l2 = self.get_licence(d2)

        rank1 = LICENCE_RANK.get(l1, 0)
        rank2 = LICENCE_RANK.get(l2, 0)

        # Most restrictive wins
        if rank1 >= rank2:
            return l1
        else:
            return l2

    def build_pipeline(self, scenario_id, excluded_datasets=None, target_licence=None):
        """
        Build a policy-compliant pipeline for a given scenario.
        Uses YAWL sequence pattern for step ordering.
        Calls checker before each merge step.
        If violation detected, triggers re-planning.
        """
        if excluded_datasets is None:
            excluded_datasets = []

        scenario = QUERY_SCENARIOS[scenario_id]
        goal = scenario["goal"]
        datasets = list(scenario["datasets"])
        operations = scenario["operations"]

        print(f"\n{'='*60}")
        print(f"PLANNING PIPELINE FOR: {goal}")
        if target_licence:
            print(f"Target output licence: {target_licence}")
        print(f"{'='*60}")

        pipeline_steps = []
        violation_info = None

        for i, operation in enumerate(operations):
            step = {
                "step": i + 1,
                "operation": operation,
                "datasets": datasets,
                "status": None
            }

            if operation == "merge" and len(datasets) >= 2:
                d1 = datasets[0]
                d2 = datasets[1]

                if d1 in excluded_datasets or d2 in excluded_datasets:
                    violated = d2 if d2 in excluded_datasets else d1
                    alt = self.find_alternative(violated, excluded_datasets)
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

                # Report what the derived licence WOULD be if this went ahead
                would_be_licence = self.derive_output_licence(d1, d2)
                print(f"  Would-be output licence: {would_be_licence}")

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
                    print(f"\n  Triggering re-planner...")
                    pipeline_steps.append(step)
                    return self.replan(
                        scenario_id, d2,
                        excluded_datasets, violation_info, target_licence
                    )
            else:
                step["status"] = "complete"
                print(f"\nStep {i+1}: {operation.upper()} - complete")

            pipeline_steps.append(step)

        # Determine derived output licence for the successful pipeline
        if len(datasets) >= 2:
            output_licence = self.derive_output_licence(datasets[0], datasets[1])
        else:
            output_licence = self.get_licence(datasets[0]) if datasets else None

        print(f"\nPIPELINE STATUS: COMPLETE ✓")
        print(f"All steps executed successfully")
        print(f"Output dataset licence: {output_licence}")
        return {
            "status": "success",
            "goal": goal,
            "pipeline": pipeline_steps,
            "datasets_used": datasets,
            "output_licence": output_licence,
            "replanned": len(excluded_datasets) > 0,
            "violation": None
        }

    def replan(self, scenario_id, violated_dataset, excluded_datasets, violation_info, target_licence=None):
        """
        Re-planning: run planner again with violated constraint as new condition.
        Finds closest achievable domain-similar alternative.
        Prevents d1==d2 degenerate merging.
        """
        print(f"\n{'-'*60}")
        print(f"RE-PLANNING...")
        print(f"Excluding: {violated_dataset}")
        print(f"Reason: {violation_info['violation_type']}")
        print(f"{'-'*60}")

        new_excluded = excluded_datasets + [violated_dataset]

        # Get the non-violated dataset in the original pair
        scenario = QUERY_SCENARIOS[scenario_id]
        original_datasets = scenario["datasets"]
        other_dataset = [d for d in original_datasets
                         if d != violated_dataset][0]

        # Find alternative - must be different from other_dataset
        alt_dataset = self.find_alternative(violated_dataset, new_excluded, target_licence)

        # Fix d1==d2 problem: if alternative is same as other dataset
        # search again excluding other_dataset as well
        if alt_dataset and alt_dataset == other_dataset:
            print(f"  Alternative matches existing dataset - searching further...")
            extended_excluded = new_excluded + [other_dataset]
            alt_dataset = self.find_alternative(
                violated_dataset, extended_excluded, target_licence
            )

        if alt_dataset:
            # Report what the derived licence will now be after re-plan
            new_derived = self.derive_output_licence(other_dataset, alt_dataset)
            print(f"Alternative found: {alt_dataset} "
                  f"({self.get_licence(alt_dataset)})")
            print(f"Re-planned output licence: {new_derived}")
            return self.build_pipeline(scenario_id, new_excluded, target_licence)
        else:
            print(f"No valid alternative found.")
            print(f"Closest achievable: pipeline with available OGL datasets")
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