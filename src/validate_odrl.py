# ============================================================
# validate_odrl.py
# Validation script for ODRL policy files
# ============================================================

from rdflib import Graph
import os

POLICY_FILES = [
    "policies/ogl_policy.ttl",
    "policies/cc_by_nc_policy.ttl",
    "policies/cc_by_sa_policy.ttl",
    "policies/odbl_policy.ttl",
]

def validate_all():
    """
    Parses each ODRL policy file using rdflib to confirm
    that it is well-formed Turtle RDF. Reports the number
    of triples in each graph.
    """
    print("=" * 60)
    print("ODRL POLICY FILE VALIDATION")
    print("=" * 60)

    all_valid = True

    for policy_path in POLICY_FILES:
        if not os.path.exists(policy_path):
            print(f"\n[MISSING] {policy_path}")
            all_valid = False
            continue

        try:
            g = Graph()
            g.parse(policy_path, format="turtle")
            n = len(g)
            print(f"\n[VALID]   {policy_path}")
            print(f"          Parsed successfully — {n} RDF triples")
        except Exception as e:
            print(f"\n[INVALID] {policy_path}")
            print(f"          Error: {e}")
            all_valid = False

    print(f"\n{'='*60}")
    if all_valid:
        print("ALL POLICY FILES ARE WELL-FORMED RDF")
    else:
        print("SOME POLICY FILES HAVE ERRORS - see above")
    print(f"{'='*60}")

    return all_valid


if __name__ == "__main__":
    validate_all()