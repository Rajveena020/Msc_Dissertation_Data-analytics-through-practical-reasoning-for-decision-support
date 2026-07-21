# ========================================================================================================================================
# baseline.py
# Static Analytics Pipeline WITHOUT Policy Awareness
# 
# This baseline runs the same query scenarios as the main system but does not check licence compliance. Its purpose is to show what happens
# when a pipeline is executed without policy reasoning - some scenarios happen to succeed by luck (compatible licences); others
#  produce licence-incorrect output silently.
# ========================================================================================================================================

import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.planner import QUERY_SCENARIOS
from src.registries import DATASET_LICENCES, get_dataset_licence
from src.checker import PolicyChecker


class BaselinePipeline:
    """
    A static pipeline that does not check licence compliance.
    
    Uses the exact same QUERY_SCENARIOS as the main planner, so what's compared like-for-like is behaviour ON THE SAME INPUTS,not different 
    scenario configurations.
    """

    def __init__(self):
        self._checker = PolicyChecker()
        self._ground_truth_violations = self._compute_ground_truth()

    def _compute_ground_truth(self):
        """
        For each scenario, compute what a policy-aware system would have flagged. Used purely for reporting the baseline's "silent misses"
        in run_all.py.
        """
        ground_truth = {}
        for scenario_id, scenario in QUERY_SCENARIOS.items():
            datasets = scenario["datasets"]
            if len(datasets) < 2:
                ground_truth[scenario_id] = None
                continue
            d1, d2 = datasets[0], datasets[1]
            l1 = get_dataset_licence(d1)
            l2 = get_dataset_licence(d2)
            result = self._checker.check(d1, l1, d2, l2)
            ground_truth[scenario_id] = (
                result["violation_type"] if not result["compliant"] else None
            )
        return ground_truth

    def run(self, scenario_id):
        """
        Execute the given scenario without any policy checking.
        
        The baseline simply loads, cleans, merges and analyses whatever datasets the scenario specifies. If they conflict, the output
        is silently licence-incorrect — no cancellation, no re-plan.
        """
        scenario = QUERY_SCENARIOS.get(scenario_id)
        if not scenario:
            return {
                "error": f"Unknown scenario: {scenario_id}"
            }

        datasets = scenario["datasets"]
        goal = scenario["goal"]

        print(f"\n{'='*55}")
        print(f"BASELINE PIPELINE: {scenario_id}")
        print(f"Goal: {goal}")
        print(f"Datasets: {datasets}")
        print(f"{'='*55}")

        # Execute pipeline steps blindly (no policy checking)
        pipeline_steps = ["load", "clean", "merge", "analyse"]
        for step in pipeline_steps:
            joined = " + ".join(datasets)
            print(f"  {step.upper()}: {joined}... COMPLETE")

        print(f"\nBASELINE STATUS: COMPLETE (no compliance check)")

        # Look up what the baseline SHOULD have flagged
        undetected = self._ground_truth_violations.get(scenario_id)

        result = {
            "status": "completed_without_checking",
            "goal": goal,
            "datasets_used": datasets,
            "undetected_violation": undetected,
            "note": (
                "This baseline did not perform any compliance check. Any 'success' here is silent — the output may or may not be licence-correct "
                "depending on whether the input datasets happened to be compatible. "  
            ),
        }

        if undetected:
            print(
                f"UNDETECTED (would be caught by system): {undetected}"
            )
        else:
            print(f"No violation would have been triggered")

        return result


# Demo 
if __name__ == "__main__":
    print("=" * 65)
    print("BASELINE DEMONSTRATION - NO POLICY CHECKING")
    print("=" * 65)
    print(
        "\nThis baseline shows what happens WITHOUT policy reasoning:"
    )
    print("  - No compliance checks")
    print("  - No re-planning")
    print("  - No cancellation region")
    print("  - Some outputs happen to be compliant by luck")
    print("  - Others are silently incorrect")
    print()

    baseline = BaselinePipeline()

    for scenario_id in QUERY_SCENARIOS.keys():
        baseline.run(scenario_id)

    print("\n" + "=" * 65)
    print("BASELINE COMPLETE")
    print("=" * 65)
    print(
        "\nCompare with the policy-aware system by running:"
    )
    print("  python evaluation/run_all.py")