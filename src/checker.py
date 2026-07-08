import clingo
import os

class PolicyChecker:
    def __init__(self, rules_path="asp/licence_rules.lp"):
        self.rules_path = rules_path
        if not os.path.exists(rules_path):
            raise FileNotFoundError(f"ASP rules file not found: {rules_path}")

    def check(self, dataset1, licence1, dataset2, licence2):
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
        violation_type = None
        explanation = None
        compliant = True
        # Note: uses string matching on the model output, which is fragile for extending to new licence types. A more robust implementation 
        # would use the clingo symbol API to iterate over model atoms directly. Documented here as a limitation.
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                atoms = str(model)
                if "violation(" in atoms:
                    compliant = False
                    if "cc_by_nc_restriction" in atoms:
                        violation_type = "cc_by_nc_restriction"
                        explanation = f"CC-BY-NC prohibits commercial use"
                    elif "share_alike_conflict" in atoms:
                        violation_type = "share_alike_conflict"
                        explanation = f"CC-BY-SA requires derived data to use same licence"
                    elif "odbl_restriction" in atoms:
                        violation_type = "odbl_restriction"
                        explanation = f"ODbL requires derived database to remain open"
                    elif "nc_sa_conflict" in atoms:
                        violation_type = "nc_sa_conflict"
                        explanation = f"CC-BY-NC and CC-BY-SA are mutually incompatible"
        # Moved outside the loop: only set the compliant explanation once, after checking all models, rather than repeatedly inside the loop.
        if compliant and violation_type is None:
            explanation = f"Combining {dataset1} with {dataset2} is compliant"

        return {"compliant": compliant, "violation_type": violation_type, "explanation": explanation, "datasets": [dataset1, dataset2]}

if __name__ == "__main__":
    checker = PolicyChecker()
    print("=" * 55)
    print("POLICY COMPLIANCE CHECKER - TEST RESULTS")
    print("=" * 55)
    r1 = checker.check("air_quality", "ogl", "nhs_admissions", "cc_by_nc")
    print(f"\nScenario 1: Compliant={r1['compliant']}, Violation={r1['violation_type']}")
    print(f"  {r1['explanation']}")
    r2 = checker.check("ons_census", "ogl", "police_crime", "ogl")
    print(f"\nScenario 2: Compliant={r2['compliant']}, Violation={r2['violation_type']}")
    print(f"  {r2['explanation']}")
    r3 = checker.check("air_quality", "ogl", "met_office_weather", "cc_by_sa")
    print(f"\nScenario 3: Compliant={r3['compliant']}, Violation={r3['violation_type']}")
    print(f"  {r3['explanation']}")
    r4 = checker.check("dft_traffic", "ogl", "osm_berkshire", "odbl")
    print(f"\nScenario 4: Compliant={r4['compliant']}, Violation={r4['violation_type']}")
    print(f"  {r4['explanation']}")
    print("\n" + "=" * 55)
