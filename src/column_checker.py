# ============================================================
# column_checker.py
# Column-Level Policy Compliance Checker (Proof of Concept)
#
# PURPOSE:
# Extends the dataset-level compliance checker to reason at the column level. Different columns within a single dataset may carry different 
# licence terms. This enables:
#   1. Fine-grained violation detection (which specific columns cause the violation)
#   2. Smarter re-planning that excludes only conflicting columns rather than entire datasets
# ============================================================

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.checker import PolicyChecker
from src.registries import COLUMN_REGISTRY, LICENCE_RANK

class ColumnLevelChecker:
    """
    Column-level policy compliance checker.

    Extends the dataset-level checker with the ability to:
      1. Identify which specific columns cause a violation
      2. Recommend which columns should be excluded to achieve compliance
      3. Report the maximum-compliant column subset
    """

    def __init__(self):
        self.checker = PolicyChecker()

    def get_column_licence(self, dataset, column):
        """Return the licence of a specific column."""
        return COLUMN_REGISTRY.get(dataset, {}).get(column)

    def get_all_columns(self, dataset):
        """Return all columns of a dataset."""
        return list(COLUMN_REGISTRY.get(dataset, {}).keys())

    def check_columns(self, dataset1, columns1, dataset2, columns2):
        """
        Check whether combining specific columns from two
        datasets violates any licence.

        Returns:
            {
                "compliant": bool,
                "violations": list of dicts describing each specific column-pair violation,
                "compliant_pairs": list of column pairs that ARE compliant and could be used in a reduced pipeline
            }
        """
        violations = []
        compliant_pairs = []

        for c1 in columns1:
            l1 = self.get_column_licence(dataset1, c1)
            for c2 in columns2:
                l2 = self.get_column_licence(dataset2, c2)

                result = self.checker.check(
                    f"{dataset1}_{c1}", l1,
                    f"{dataset2}_{c2}", l2
                )

                if not result["compliant"]:
                    violations.append({
                        "column1":       f"{dataset1}.{c1}",
                        "licence1":      l1,
                        "column2":       f"{dataset2}.{c2}",
                        "licence2":      l2,
                        "violation_type": result["violation_type"]
                    })
                else:
                    compliant_pairs.append({
                        "column1": f"{dataset1}.{c1}",
                        "column2": f"{dataset2}.{c2}",
                        "licence1": l1,
                        "licence2": l2
                    })

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "compliant_pairs": compliant_pairs,
            "total_pairs_checked": len(columns1) * len(columns2)
        }

    def find_compliant_columns(self, dataset1, dataset2):
        """
        Given two datasets, identify the maximum subset of columns from each that can be safely combined without violating any licence.

        Strategy: iteratively remove the column that appears in the most violations, from whichever dataset it belongs to. This handles
        scenarios where both datasets carry restrictive columns that conflict with each other - a case that a single-direction
        shrinking algorithm cannot recover.
        """
        cols1 = self.get_all_columns(dataset1)
        cols2 = self.get_all_columns(dataset2)
        

        safe_cols1 = list(cols1)
        safe_cols2 = list(cols2)
        excluded_cols1 = []
        excluded_cols2 = []

        while True:
            result = self.check_columns(
                dataset1, safe_cols1, dataset2, safe_cols2
            )
           
            if result["compliant"]:
                # If either safe list is empty, treat as no viable subset.
                if not safe_cols1 or not safe_cols2:
                    return {
                        "safe_columns_dataset1": [],
                        "safe_columns_dataset2": [],
                        "excluded_columns_dataset1": cols1,
                        "excluded_columns_dataset2": cols2,
                        "reduction_dataset1": (
                            f"0/{len(cols1)} columns preserved"
                        ),
                        "reduction_dataset2": (
                            f"0/{len(cols2)} columns preserved"
                        ),
                        "direction_chosen": "none",
                    }
                # Otherwise, report the successful shrink.
                direction = self._describe_direction(
                    excluded_cols1, excluded_cols2
                )
                return {
                    "safe_columns_dataset1": safe_cols1,
                    "safe_columns_dataset2": safe_cols2,
                    "excluded_columns_dataset1": excluded_cols1,
                    "excluded_columns_dataset2": excluded_cols2,
                    "reduction_dataset1": (
                        f"{len(safe_cols1)}/{len(cols1)} columns preserved"
                    ),
                    "reduction_dataset2": (
                        f"{len(safe_cols2)}/{len(cols2)} columns preserved"
                    ),
                    "direction_chosen": direction,
                }

            # Count how often each column appears in violations.
            # Score each column that appears in a violation by:
            #   (a) restrictiveness of its licence (higher rank = removed first)
            #   (b) number of violations it appears in
            # Then remove the single worst-scoring column across both datasets.
            candidates = []

            for v in result["violations"]:
                c1 = v["column1"].split(".")[1]
                c2 = v["column2"].split(".")[1]
                l1 = v["licence1"]
                l2 = v["licence2"]
                candidates.append((1, c1, l1))
                candidates.append((2, c2, l2))

            # Aggregate: count occurrences per (dataset, column, licence).
            score = {}
            for (ds, col, lic) in candidates:
                key = (ds, col, lic)
                score[key] = score.get(key, 0) + 1

            # Rank by (licence_rank, violation_count) descending. The  more restrictive the licence, the earlier the column goes;
            # ties broken by count.
            def sort_key(item):
                (ds, col, lic), count = item
                rank = LICENCE_RANK.get(lic, 0)
                return (rank, count)

            best = max(score.items(), key=sort_key, default=None)
            if best is None:
                break

            (ds, col, lic), _ = best
            if ds == 1:
                safe_cols1.remove(col)
                excluded_cols1.append(col)
            else:
                safe_cols2.remove(col)
                excluded_cols2.append(col)

            # If either safe list becomes empty, stop.
            if not safe_cols1 or not safe_cols2:
                return {
                    "safe_columns_dataset1": [],
                    "safe_columns_dataset2": [],
                    "excluded_columns_dataset1": cols1,
                    "excluded_columns_dataset2": cols2,
                    "reduction_dataset1": (
                        f"0/{len(cols1)} columns preserved"
                    ),
                    "reduction_dataset2": (
                        f"0/{len(cols2)} columns preserved"
                    ),
                    "direction_chosen": "none",
                }

    def _describe_direction(self, excluded_d1, excluded_d2):
        """
        Report which direction(s) the algorithm shrunk.
        """
        if excluded_d1 and excluded_d2:
            return "shrink_both"
        elif excluded_d2:
            return "shrink_dataset2"
        elif excluded_d1:
            return "shrink_dataset1"
        else:
            return "no_shrink_needed"

# Demo Scenarios 
if __name__ == "__main__":
    ccc = ColumnLevelChecker()

    print("=" * 70)
    print("COLUMN-LEVEL COMPLIANCE CHECKER - PROOF OF CONCEPT")
    print("=" * 70)

    # Demo 1: Fine-grained detection 
    print("\n" + "-" * 70)
    print("DEMO 1: Fine-Grained Violation Detection")
    print("-" * 70)
    print("Dataset-level check for air_quality + nhs_admissions:")
    print("  → Reports a single OGL + CC-BY-NC violation")
    print("  → Recommends excluding the ENTIRE nhs_admissions dataset")
    print("\nColumn-level check for the same combination:")

    result = ccc.check_columns(
        "air_quality",
        ["date", "pm10", "no2", "region"],
        "nhs_admissions",
        ["hospital_code", "admission_date", "region",
         "diagnosis_code", "age_group"]
    )

    print(f"\n  Total column pairs checked: {result['total_pairs_checked']}")
    print(f"  Compliant pairs:            {len(result['compliant_pairs'])}")
    print(f"  Violating pairs:            {len(result['violations'])}")

    if result["violations"]:
        print("\n  Column-level violations:")
        for v in result["violations"][:5]:
            print(f"    {v['column1']} ({v['licence1']})"
                  f" + {v['column2']} ({v['licence2']})"
                  f" → {v['violation_type']}")
        if len(result["violations"]) > 5:
            print(f"    ... and {len(result['violations'])-5} more")

    # Demo 2: Maximum-compliant column subset 
    print("\n" + "-" * 70)
    print("DEMO 2: Maximum-Compliant Column Subset")
    print("-" * 70)
    print("Instead of excluding nhs_admissions entirely, identify which columns CAN safely be combined: ")

    subset = ccc.find_compliant_columns("air_quality", "nhs_admissions")

    print(f"\n  air_quality:    {subset['reduction_dataset1']}")
    print(f"    Safe columns:      {subset['safe_columns_dataset1']}")
    print(f"    Excluded columns:  {subset['excluded_columns_dataset1']}")

    print(f"\n  nhs_admissions: {subset['reduction_dataset2']}")
    print(f"    Safe columns:      {subset['safe_columns_dataset2']}")
    print(f"    Excluded columns:  {subset['excluded_columns_dataset2']}")

    # Demo 3: Comparison with dataset-level checker
    print("\n" + "-" * 70)
    print("DEMO 3: Comparison with Dataset-Level Approach")
    print("-" * 70)
    print("Dataset-level checker:")
    print("  air_quality (OGL) + nhs_admissions (CC-BY-NC)")
    print("  → VIOLATION → exclude entire nhs_admissions dataset")
    print("  → Data lost: ALL 8 columns of nhs_admissions")
    print()
    print("Column-level checker:")
    n_safe = len(subset['safe_columns_dataset2'])
    n_total = len(ccc.get_all_columns("nhs_admissions"))
    print(f"  → VIOLATION detected on {n_total - n_safe} specific columns")
    print(f"  → Exclude only conflicting columns:"
          f" {subset['excluded_columns_dataset2']}")
    print(f"  → Data preserved: {n_safe}/{n_total} columns"
          f" of nhs_admissions")

    print("\n" + "=" * 70)
    print("CONCLUSION: Column-level checking preserves more data")
    print("while maintaining full policy compliance.")
    print("=" * 70)
