# ============================================================
# planner.py - Pipeline Planner with YAWL patterns
# 
# Includes:
# - YAWL-grounded workflow patterns 
# - Column-level compliance fallback (proof of concept)
# - Structured re-planning trace
# ============================================================

import clingo
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.checker import PolicyChecker
from src.column_checker import ColumnLevelChecker

from src.registries import (
    DATASET_LICENCES,
    DOMAIN_ALTERNATIVES,
    LICENCE_RANK,
    get_dataset_licence,
)


# Constraint Tracking for Re-planning 
_REPLANNING_CONSTRAINTS = {}


def get_constraints(scenario_id):
    """Get accumulated constraints for a scenario"""
    return _REPLANNING_CONSTRAINTS.get(scenario_id, [])


def add_constraint(scenario_id, dataset):
    """Add a dataset to the exclusion list for a scenario"""
    if scenario_id not in _REPLANNING_CONSTRAINTS:
        _REPLANNING_CONSTRAINTS[scenario_id] = []
    if dataset not in _REPLANNING_CONSTRAINTS[scenario_id]:
        _REPLANNING_CONSTRAINTS[scenario_id].append(dataset)


def reset_constraints(scenario_id):
    """Reset constraints for a fresh planning run"""
    _REPLANNING_CONSTRAINTS[scenario_id] = []


# Query Scenarios (User Analytics Goals)
QUERY_SCENARIOS = {
    "scenario_1": {
        "goal": "Analyse effect of air quality on hospital admissions",
        "datasets": ["air_quality", "nhs_admissions"]
    },
    "scenario_2": {
        "goal": "Compare local authority census data with crime statistics",
        "datasets": ["ons_census", "police_crime"]
    },
    "scenario_3": {
        "goal": "Study relationship between weather and traffic incidents",
        "datasets": ["dft_traffic", "met_office_weather"]
    },
    "scenario_4": {
        "goal": "Analyse hospital admissions correlated with weather patterns",
        "datasets": ["met_office_weather", "nhs_admissions"]
    },
    "scenario_5": {
        "goal": "Study impact of geographic data on traffic patterns",
        "datasets": ["dft_traffic", "osm_berkshire"]
    },
    "scenario_6": {
        "goal": "Analyse weather patterns for scientific publication (needs CC-BY-SA)",
        "datasets": ["met_office_weather", "met_office_weather"],
        "target_licence": "cc_by_sa"
    },
    "scenario_7": {
        "goal": "Analyse impact of geospatial data on hospital admissions",
        "datasets": ["osm_berkshire", "nhs_admissions"]
    }
}


# YAWL-Grounded Pipeline Patterns
PIPELINE_STEPS = ["load", "clean", "merge", "analyse"]

class PipelinePlanner:
    def __init__(
        self,
        rules_path="asp/licence_rules.lp",
        use_column_level=False
    ):
        self.rules_path = rules_path
        self.checker = PolicyChecker(rules_path)
        self.column_checker = ColumnLevelChecker()
        self.use_column_level = use_column_level

    def get_licence(self, dataset):
        """Return the licence of a dataset from the shared registry."""
        return get_dataset_licence(dataset)

    def derive_output_licence(self, dataset1, dataset2, target_licence=None):
        """
        Determine the licence of the combined output dataset. Uses the 'most restrictive wins' rule. Return None if the combination 
        itself is a violation.
        """
        l1 = self.get_licence(dataset1)
        l2 = self.get_licence(dataset2)

        # If a target licence is explicitly requested (e.g. CC-BY-SA for a share-alike publication), return that if both inputs are compatible
        # with producing it
        if target_licence and l1 == target_licence and l2 == target_licence:
            return target_licence

        rank1 = LICENCE_RANK.get(l1, 0)
        rank2 = LICENCE_RANK.get(l2, 0)

        return l1 if rank1 >= rank2 else l2

    def derive_output_licence_from_columns(self, d1, d2, retained_columns_d2):
        """
        Compute the derived licence based on the RETAINED columns after column-level compliance filtering.

        This addresses a critical correctness issue: when the column-level checker excludes all restricted columns of a dataset, the output
        should NOT inherit that dataset's original licence - it should reflect the licences of the columns actually kept.
        """
        # Start with d1's licence (whole dataset used)
        licences_in_use = {self.get_licence(d1)}

        # Add licences of retained columns from d2
        for col in retained_columns_d2:
            col_licence = self.column_checker.get_column_licence(d2, col)
            if col_licence:
                licences_in_use.add(col_licence)

        # Find the most restrictive licence among those in use
        most_restrictive = None
        highest_rank = -1
        for lic in licences_in_use:
            rank = LICENCE_RANK.get(lic, 0)
            if rank > highest_rank:
                highest_rank = rank
                most_restrictive = lic

        return most_restrictive

    def build_pipeline(self, scenario_id, _new_datasets=None):
        """
        Build a pipeline plan for a scenario using YAWL patterns.

        When use_column_level=True, column-level compliance is tried FIRST as the PRIMARY  strategy for preserving data.
        Dataset-level substitution is used as a fallback only when column-level fails to find a compatible subset.
        This restores the intended narrative of the column-level checker as the principal contribution rather than a rarely-triggered fallback.        
        """
        # Handle re-plan case (recursion signal)
        if _new_datasets:
            scenario = QUERY_SCENARIOS[scenario_id.split("_replan")[0]]
            scenario = {
                "goal":     scenario["goal"],
                "datasets": _new_datasets
            }
        else:
            scenario = QUERY_SCENARIOS.get(scenario_id)
            if not scenario:
                return {"error": f"Unknown scenario: {scenario_id}"}
            # Reset constraints for fresh pipeline run
            if not _new_datasets:
                reset_constraints(scenario_id)

        d1, d2 = scenario["datasets"]
        l1 = self.get_licence(d1)
        l2 = self.get_licence(d2)

        print(f"\n{'='*55}")
        print(f"Query: {scenario['goal']}")
        print(f"Datasets: {d1} ({l1}) + {d2} ({l2})")
        print(f"{'='*55}")

        # YAWL cancellation region: check policy before executing
        print(f"\nPRE-PIPELINE POLICY CHECK...")
        pre_check = self.checker.check(d1, l1, d2, l2)

        if not pre_check["compliant"]:
            print(f"CANCELLATION TRIGGERED (YAWL pattern)")
            print(f"Violation: {pre_check['violation_type']}")
            print(f"Reason: {pre_check['explanation']}")

            base_scenario_id = scenario_id.split("_replan")[0]

        
            if self.use_column_level:
                print(f"\nATTEMPTING COLUMN-LEVEL COMPLIANCE "
                      f"(primary strategy)...")

                col_result = self.column_checker.find_compliant_columns(
                    d1, d2
                )

                # Column-level succeeds if we retain at least one column from each dataset
               
                safe_d1 = col_result.get("safe_columns_dataset1", [])
                safe_d2 = col_result.get("safe_columns_dataset2", [])
                
                if safe_d1 and safe_d2:
                    # Verify: check that the retained subset is actually compliant (not vacuously so)
                
                    verification = self.column_checker.check_columns(
                        d1, safe_d1, d2, safe_d2
                    )
                    
                    if verification["compliant"] and \
                       verification["total_pairs_checked"] > 0:
                        print(f"\nColumn-level compliance identified:")
                        print(f"  Preserved from {d1}: "
                              f"{col_result['reduction_dataset1']}")
                        print(f"  Preserved from {d2}: "
                              f"{col_result['reduction_dataset2']}")

                        # Derive output licence from retained columns
                        output_licence = \
                            self.derive_output_licence_from_columns(
                                d1, d2, safe_d2
                            )
                        print(f"\nPIPELINE STATUS: COMPLETE ✓")
                        print(f"Column-level compliance achieved")
                        print(f"Output dataset licence: "
                              f"{output_licence} "
                              f"(derived from retained columns)")

                        return {
                            "status":           "success",
                            "compliance_mode":  "column_level",
                            "column_subset":    col_result,
                            "output_licence":   output_licence,
                            "datasets_used":    [d1, d2],
                            "goal":             scenario["goal"],
                            "yawl_pattern_used":
                                "cancellation-region-with-column-primary",
                            "replan_trace": {
                                "original_datasets": [d1, d2],
                                "swapped_out":       None,
                                "swapped_in":        None,
                                "reason":            pre_check["violation_type"],
                                "explanation":       pre_check["explanation"],
                                "strategy":          "column_level_primary",
                                "columns_preserved":
                                    safe_d2,
                                "columns_excluded":
                                    col_result["excluded_columns_dataset2"]
                            }
                        }
                
                print(f"Column-level compliance could not "
                      f"preserve a compatible subset")

            # ================================================
            # FALLBACK STRATEGY: dataset-level substitution
            # (used when column-level unavailable or fails)
            # ================================================
            print(f"\nATTEMPTING DATASET-LEVEL SUBSTITUTION "
                  f"(fallback strategy)...")
            print(f"Adding constraint: exclude {d2}")

            add_constraint(base_scenario_id, d2)
            result = self.replan(d1, d2, pre_check, base_scenario_id)

            if result["status"] == "success":
                print(f"Alternative found: {result['alternative']}")
                # Continue with alternative dataset
                final_result = self.build_pipeline(
                    scenario_id + "_replan",
                    _new_datasets=result["new_datasets"]
                )
                final_result["replan_trace"] = {
                    "original_datasets": [d1, d2],
                    "swapped_out":       d2,
                    "swapped_in":        result["alternative"],
                    "reason":            pre_check["violation_type"],
                    "explanation":       pre_check["explanation"],
                    "strategy":          "domain_similar_substitution"
                }
                final_result["replanned"] = True
                return final_result
            else:
                # Both strategies failed
                print(f"\nPIPELINE STATUS: PARTIAL")
                print(f"Reason: {result['reason']}")
                return {
                    "status":            "partial",
                    "goal":              scenario["goal"],
                    "reason":            result["reason"],
                    "cancellation_from": [d1, d2],
                    "yawl_pattern_used": "cancellation-region",
                    "replan_trace": {
                        "original_datasets": [d1, d2],
                        "swapped_out":       None,
                        "swapped_in":        None,
                        "reason":            pre_check["violation_type"],
                        "explanation":       pre_check["explanation"],
                        "strategy":          "no_alternative_found"
                    }
                }

        # No violation - execute pipeline in sequence
        return self._execute_pipeline(d1, d2, scenario)

    def _execute_pipeline(self, d1, d2, scenario):
        """
        Execute the pipeline (YAWL: sequence pattern). This is only reached if the policy check passed.
        """
        print(f"\nPOLICY CHECK PASSED - EXECUTING PIPELINE")
        print(f"YAWL Pattern: SEQUENCE")

        target_licence = scenario.get("target_licence")

        for step in PIPELINE_STEPS:
            print(f"  {step.upper()}: {d1} + {d2}... COMPLETE")

        output_licence = self.derive_output_licence(d1, d2, target_licence)
        print(f"\nPIPELINE STATUS: COMPLETE")
        print(f"Compliance verified via ODRL 2.2 policies")
        print(f"Output dataset licence: {output_licence} ")

        return {
            "status":          "success",
            "compliance_mode": "dataset_level",
            "output_licence":  output_licence,
            "target_licence":  target_licence,
            "datasets_used":   [d1, d2],
            "goal":            scenario["goal"],
            "yawl_pattern_used": "sequence"
        }

    def replan(self, d1, d2, violation, scenario_id):
        """
        Try to find an alternative for the violated dataset. 
        YAWL Pattern: XOR-split (choose one alternative) 
        With re-planning: constraint accumulation
        Returns structured info about the alternative found.
        """
        # Get accumulated constraints for this scenario
        accumulated_constraints = get_constraints(scenario_id)
        print(f"Accumulated constraints for {scenario_id}: "
              f"exclude {accumulated_constraints}")

        # Try alternatives for d2 (excluding all accumulated)
        alternatives = DOMAIN_ALTERNATIVES.get(d2, [])

        for alt in alternatives:
            # Skip if this alternative is in the exclusion list
            if alt in accumulated_constraints:
                print(f"Skipping {alt} (already excluded)")
                continue

            print(f"Testing alternative: {alt}")
            alt_licence = self.get_licence(alt)
            alt_check = self.checker.check(d1, self.get_licence(d1),
                                           alt, alt_licence)

            if alt_check["compliant"]:
                return {
                    "status":         "success",
                    "alternative":    alt,
                    "new_datasets":   [d1, alt],
                    "alt_licence":    alt_licence,
                }
            else:
                # Constraint accumulation: add THIS failure too
                add_constraint(scenario_id, alt)
                print(f"  Failed: {alt_check['violation_type']}")

        return {
            "status": "failed",
            "reason": "No compliant alternative found for {d2}",
            "constraints_tried": get_constraints(scenario_id)
        }


# Demo 
if __name__ == "__main__":
    print("=" * 65)
    print("PIPELINE PLANNER DEMO")
    print("=" * 65)

    planner = PipelinePlanner()

    for scenario_id in QUERY_SCENARIOS.keys():
        result = planner.build_pipeline(scenario_id)
        print(f"\nResult: {result['status']}")
        if result.get("replan_trace"):
            trace = result["replan_trace"]
            if trace["swapped_out"]:
                print(f"  Swapped: {trace['swapped_out']} -> "
                      f"{trace['swapped_in']}")
                print(f"  Reason: {trace['reason']}")
            print(f"  Strategy: {trace['strategy']}")