# ============================================================
# run_all.py
# Formal Evaluation Script - System vs Baseline Comparison
# Including column-level vs dataset-level comparison
# ============================================================

import sys
import os
import csv
import time
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

from src.planner import PipelinePlanner
from src.checker import PolicyChecker
from src.column_checker import ColumnLevelChecker
from evaluation.baseline import BaselinePipeline

RESULTS_FILE = os.path.join("evaluation", "results.csv")


def verify_dataset_level_pipeline(result):
    """
    Returns True if the final pair is compliant, False otherwise. Handles the 'partial' case (no alternative found) - this is correct behaviour
    per Objective O4, so counts as licence-correct.
    """
    checker = PolicyChecker()
    
    if result["status"] == "partial":
        return True
    
    datasets_used = result.get("datasets_used", [])
    if len(datasets_used) < 2:
        # Not a merge scenario; nothing to verify
        return True
    
    d1, d2 = datasets_used[0], datasets_used[1]
    planner = PipelinePlanner()
    l1 = planner.get_licence(d1)
    l2 = planner.get_licence(d2)
    
    check_result = checker.check(d1, l1, d2, l2)
    return check_result["compliant"]


def verify_column_level_pipeline(result):
    """
    Verify that a column-level pipeline's final output is genuinely licence-correct.
    
    For column-level mode: verify that the RETAINED columns of the restricted dataset are compatible with the other dataset.
    For dataset-level fallback: same as dataset-level verification.
    """
    # Partial: system correctly reported no alternative
    if result["status"] == "partial":
        return True
    
    # If column-level compliance was used, verify the retained columns
    if result.get("compliance_mode") == "column_level":
        col_checker = ColumnLevelChecker()
        subset = result.get("column_subset", {})
        datasets = result.get("datasets_used", [])
        
        if len(datasets) < 2:
            return True
        
        d1, d2 = datasets[0], datasets[1]
        safe_cols_d1 = subset.get("safe_columns_dataset1", [])
        safe_cols_d2 = subset.get("safe_columns_dataset2", [])
        
        # If no safe columns registered for d1, use all columns
        if not safe_cols_d1:
            safe_cols_d1 = col_checker.get_all_columns(d1)
        
        # Verify no violations remain in the retained subset
        check_result = col_checker.check_columns(
            d1, safe_cols_d1, d2, safe_cols_d2
        )
        return check_result["compliant"]
    
    # Otherwise: dataset-level fallback, verify normally
    return verify_dataset_level_pipeline(result)


def verify_baseline_pipeline(scenario_id, baseline_result):
    """
    Verify the baseline's output claim against the actual licence status of the datasets it used.
    The baseline never checks compliance, so its output is licence-correct only when the input datasets happen to be compliant with each other
    by luck.
    """
    from src.planner import QUERY_SCENARIOS
    scenario = QUERY_SCENARIOS[scenario_id]
    datasets = scenario["datasets"]
    
    if len(datasets) < 2:
        return True
    
    checker = PolicyChecker()
    planner = PipelinePlanner()
    d1, d2 = datasets[0], datasets[1]
    l1 = planner.get_licence(d1)
    l2 = planner.get_licence(d2)
    
    result = checker.check(d1, l1, d2, l2)
    return result["compliant"]


def calculate_preservation(col_result):
    """
    Report column preservation for column-level compliance. The bidirectional algorithm may shrink either dataset, so both  dataset1 and dataset2
    preservation are reported.
    """
    if col_result.get("compliance_mode") == "column_level":
        subset = col_result.get("column_subset", {})
        safe_d1 = len(subset.get("safe_columns_dataset1", []))
        excl_d1 = len(subset.get("excluded_columns_dataset1", []))
        safe_d2 = len(subset.get("safe_columns_dataset2", []))
        excl_d2 = len(subset.get("excluded_columns_dataset2", []))
        total_d1 = safe_d1 + excl_d1
        total_d2 = safe_d2 + excl_d2
        return f"d1:{safe_d1}/{total_d1}, d2:{safe_d2}/{total_d2}"
    return "N/A (re-planned)"


def calculate_loss(ds_result):
    """
    Calculate data loss for dataset-level re-planning.
    """
    if ds_result.get("replanned"):
        return "100% of violated dataset excluded"
    return "None (compliant)"


def run_evaluation():
    """
    Runs all scenarios on:
    1. Policy-aware system (dataset-level compliance)
    2. Policy-aware system (column-level compliance)
    3. Static baseline (no checking)
    """
    ds_planner  = PipelinePlanner(use_column_level=False)
    col_planner = PipelinePlanner(use_column_level=True)
    baseline    = BaselinePipeline()

    scenarios = [
        "scenario_1",
        "scenario_2",
        "scenario_3",
        "scenario_4",
        "scenario_5",
        "scenario_6",
        "scenario_7",
    ]

    rows = []

    print("=" * 65)
    print("FORMAL EVALUATION - SYSTEM VS BASELINE")
    print("Correctness verified post-hoc")
    print("=" * 65)

    for scenario_id in scenarios:
        print(f"\n{'-'*65}")
        print(f"Evaluating {scenario_id}...")
        print(f"{'-'*65}")

        # Run 1: dataset-level compliance
        start = time.time()
        ds_result = ds_planner.build_pipeline(scenario_id)
        ds_time = round(time.time() - start, 4)
        # POST-HOC VERIFICATION
        ds_verified = verify_dataset_level_pipeline(ds_result)

        # Run 2: column-level compliance
        start = time.time()
        col_result = col_planner.build_pipeline(scenario_id)
        col_time = round(time.time() - start, 4)
        # POST-HOC VERIFICATION
        col_verified = verify_column_level_pipeline(col_result)

        # Run 3: baseline (no checking)
        start = time.time()
        baseline_result = baseline.run(scenario_id)
        baseline_time = round(time.time() - start, 4)
        # POST-HOC VERIFICATION (independent of baseline's own claim)
        baseline_verified = verify_baseline_pipeline(
            scenario_id, baseline_result
        )
        baseline_violation = baseline_result.get(
            "undetected_violation"
        )

        # Record verified results
        row = {
            "scenario":                    scenario_id,
            "goal":                        ds_result["goal"],

            # Dataset-level system
            "ds_status":                   ds_result["status"],
            "ds_licence_correct":          ds_verified,  # VERIFIED
            "ds_replanned":                ds_result.get("replanned", False),
            "ds_data_loss":                calculate_loss(ds_result),
            "ds_output_licence":           ds_result.get(
                                              "output_licence", "N/A"
                                          ),
            "ds_time_seconds":             ds_time,

            # Column-level system
            "col_status":                  col_result["status"],
            "col_licence_correct":         col_verified,  # VERIFIED
            "col_compliance_mode":         col_result.get(
                                              "compliance_mode",
                                              "dataset_level"
                                          ),
            "col_data_preserved":          calculate_preservation(col_result),
            "col_output_licence":          col_result.get(
                                              "output_licence", "N/A"
                                          ),
            "col_time_seconds":            col_time,

            # Baseline
            "baseline_licence_correct":    baseline_verified,  # VERIFIED
            "baseline_undetected":         baseline_violation,
            "baseline_time_seconds":       baseline_time,
        }
        rows.append(row)

    # Write to CSV
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Print summary
    print(f"\n{'='*65}")
    print(f"EVALUATION COMPLETE - Results saved to: {RESULTS_FILE}")
    print(f"{'='*65}")

    print(
        f"\n{'Scenario':<12} {'Dataset-Level':^22} "
        f"{'Column-Level':^22} {'Baseline':^12}"
    )
    print(f"{'-'*68}")

    for row in rows:
        # Dataset-level
        if row["ds_licence_correct"]:
            ds_ok = "Correct"
            if row["ds_replanned"]:
                ds_ok += " (re-planned)"
        else:
            ds_ok = "INCORRECT"

        # Column-level
        col_mode = row["col_compliance_mode"]
        if row["col_licence_correct"]:
            col_ok = "Correct"
            if col_mode == "column_level":
                col_ok += f" (col:{row['col_data_preserved']})"
        else:
            col_ok = "INCORRECT"

        # Baseline
        if row["baseline_licence_correct"] is None:
            bl_ok = "N/A"
        elif row["baseline_licence_correct"]:
            bl_ok = "Correct"
        else:
            bl_ok = "INCORRECT"

        print(
            f"{row['scenario']:<12} {ds_ok:<22} "
            f"{col_ok:<22} {bl_ok:<12}"
        )

    print(f"\nSUMMARY (all figures verified post-hoc):")
    ds_correct = sum(1 for r in rows if r["ds_licence_correct"])
    ds_replanned = sum(1 for r in rows if r["ds_replanned"])
    col_correct = sum(1 for r in rows if r["col_licence_correct"])
    col_level_used = sum(
        1 for r in rows
        if r["col_compliance_mode"] == "column_level"
    )
    bl_correct = sum(
        1 for r in rows
        if r["baseline_licence_correct"] is True
    )
    bl_total = len(rows)

    print(
        f"  Dataset-level  - Licence-correct: {ds_correct}/{len(rows)}"
        f" | Re-planned: {ds_replanned}/{len(rows)}"
    )
    print(
        f"  Column-level   - Licence-correct: {col_correct}/{len(rows)}"
        f" | Column-level used: {col_level_used}/{len(rows)}"
    )
    print(
        f"  Baseline       - Licence-correct: {bl_correct}/{bl_total}"
        f" | Violations missed: {bl_total-bl_correct}/{bl_total}"
    )
    print(f"{'='*65}")


if __name__ == "__main__":
    run_evaluation()