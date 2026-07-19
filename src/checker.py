import clingo
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))
from src.registries import VALID_LICENCES

# Machine-readable explanations for each violation type. 
VIOLATION_EXPLANATIONS = {
    "cc_by_nc_restriction":
        "CC-BY-NC prohibits commercial use",
    "share_alike_conflict":
        "CC-BY-SA requires derived data to use same licence",
    "odbl_restriction":
        "ODbL requires derived database to remain open",
    "nc_sa_conflict":
        "CC-BY-NC and CC-BY-SA are mutually incompatible",
    "sa_odbl_conflict":
        "CC-BY-SA and ODbL have incompatible share-alike scopes",
    "nc_odbl_conflict":
        "CC-BY-NC and ODbL are mutually incompatible",
    "unknown_pair":
        "No explicit compatibility rule for this licence pair",
}


class PolicyChecker:
    def __init__(self, rules_path="asp/licence_rules.lp"):
        self.rules_path = rules_path
        if not os.path.exists(rules_path):
            raise FileNotFoundError(f"ASP rules file not found: {rules_path}")

    def check(self, dataset1, licence1, dataset2, licence2):
        # If a column is not in the COLUMN_REGISTRY, its licence comes back as None. Passing None directly into the ASP facts crashes clingo,
        # because "None" starts with an uppercase letter and is parsed as an unsafe variable.
        
        if licence1 is None or licence2 is None:
            missing = dataset1 if licence1 is None else dataset2
            return {
                "compliant": False,
                "violation_type": "missing_licence",
                "explanation": (
                    f"No licence information available for '{missing}'. The dataset or column is not registered in the licence catalogue. "
                ),
                "datasets": [dataset1, dataset2],
                "all_violations": []
            }

        if licence1 not in VALID_LICENCES or licence2 not in VALID_LICENCES:
            unknown = (
                licence1
                if licence1 not in VALID_LICENCES
                else licence2
            )
            return {
                "compliant": False,
                "violation_type": "unknown_licence",
                "explanation": (
                    f"Licence '{unknown}' is not recognised. "
                    f"Supported licences: {sorted(VALID_LICENCES)}."
                ),
                "datasets": [dataset1, dataset2],
                "all_violations": []
            }

        # Build ASP facts and run the solver
        facts = f"""
            dataset({dataset1}).
            dataset({dataset2}).
            licence({dataset1}, {licence1}).
            licence({dataset2}, {licence2}).
            combine({dataset1}, {dataset2}).
        """
        ctl = clingo.Control()
        ctl.load(self.rules_path)
        ctl.add("base", [], facts)
        ctl.ground([("base", [])])

        all_violations = []
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                for atom in model.symbols(atoms=True):
                    if atom.name == "violation":
                        # violation(D1, D2, ViolationType)
                        d1 = str(atom.arguments[0])
                        d2 = str(atom.arguments[1])
                        vtype = str(atom.arguments[2])
                        all_violations.append({
                            "dataset1": d1,
                            "dataset2": d2,
                            "violation_type": vtype
                        })
                # Only need the first stable model
                break

        # Derive top-level result
        if all_violations:
            primary = all_violations[0]
            return {
                "compliant": False,
                "violation_type": primary["violation_type"],
                "explanation": VIOLATION_EXPLANATIONS.get(
                    primary["violation_type"],
                    f"Unknown violation type: {primary['violation_type']}"
                ),
                "datasets": [dataset1, dataset2],
                "all_violations": all_violations
            }

        return {
            "compliant": True,
            "violation_type": None,
            "explanation": (
                f"Combining {dataset1} with {dataset2} is compliant"
            ),
            "datasets": [dataset1, dataset2],
            "all_violations": []
        }


if __name__ == "__main__":
    checker = PolicyChecker()
    print("=" * 55)
    print("POLICY COMPLIANCE CHECKER - TEST RESULTS")
    print("=" * 55)

    r1 = checker.check("air_quality", "ogl",
                       "nhs_admissions", "cc_by_nc")
    print(f"\nScenario 1: Compliant={r1['compliant']}, "
          f"Violation={r1['violation_type']}")
    print(f"  {r1['explanation']}")

    r2 = checker.check("ons_census", "ogl",
                       "police_crime", "ogl")
    print(f"\nScenario 2: Compliant={r2['compliant']}, "
          f"Violation={r2['violation_type']}")
    print(f"  {r2['explanation']}")

    r3 = checker.check("air_quality", "ogl",
                       "met_office_weather", "cc_by_sa")
    print(f"\nScenario 3: Compliant={r3['compliant']}, "
          f"Violation={r3['violation_type']}")
    print(f"  {r3['explanation']}")

    r4 = checker.check("dft_traffic", "ogl",
                       "osm_berkshire", "odbl")
    print(f"\nScenario 4: Compliant={r4['compliant']}, "
          f"Violation={r4['violation_type']}")
    print(f"  {r4['explanation']}")

    # Issue 5 defensive-programming demo
    r5 = checker.check("dataset_x", "ogl", "dataset_y", None)
    print(f"\nScenario 5 (missing licence): Compliant={r5['compliant']}, "
          f"Violation={r5['violation_type']}")
    print(f"  {r5['explanation']}")

    print("\n" + "=" * 55)