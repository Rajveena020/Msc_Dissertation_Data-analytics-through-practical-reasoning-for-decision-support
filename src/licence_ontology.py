# ============================================================
# licence_ontology.py
# Licence Ontology with Lattice-Based Derived Licence Reasoning
#
# PURPOSE:
# Implements a licence ontology withformal hierarchy and least-upper-bound (LUB) queries for computing the derived licence of combined datasets.
#
# Key insight: when the LUB query returns "unknown" (no coherent single derived licence exists), the system falls  back to the column-level
# compliance checker - connecting the two main contributions of this dissertation.
#
# This is a simplified proof of concept. A production versionwould use OWL (Web Ontology Language) with a description logic reasoner
#  such as HermiT or Pellet.
# ============================================================

# Multi-dimensional restrictiveness structure.
#
# Licences differ along multiple axes:
#   - Attribution (all require it)
#   - Share-alike constraint (CC-BY-SA, ODbL)
#   - Non-commercial constraint (CC-BY-NC)
#
# When two licences constrain along the SAME axis, one may subsume the other. When they constrain along DIFFERENT axes,  no coherent single
# derived licence exists - the query returns "unknown" and the system falls back to column-level.

LICENCE_HIERARCHY = {
    "ogl":             "any_licence",
    "cc_by":           "ogl",
    "cc_by_sa":        "cc_by",       # adds share-alike axis
    "odbl":            "cc_by",       # adds database share-alike axis
    "cc_by_nc":        "cc_by",       # adds non-commercial axis
    "any_licence":     None,          # root
}

# Human-readable descriptions
LICENCE_DESCRIPTIONS = {
    "ogl":            "Open Government Licence v3.0",
    "cc_by":          "Creative Commons Attribution 4.0",
    "cc_by_sa":       "Creative Commons Attribution-ShareAlike 4.0",
    "cc_by_nc":       "Creative Commons Attribution-NonCommercial 4.0",
    "odbl":           "Open Data Commons Open Database Licence 1.0",
    "any_licence":    "(abstract) Root - any licence",
}


class LicenceOntology:
    """
    Licence ontology with least-upper-bound (LUB) queries.

    Given two licences, computes the derived licence for their combination using the formal lattice hierarchy.

    Returns:
    - A concrete licence if one subsumes the other along the same constraint axis "unknown" if the two licences add incompatible
      constraint types (e.g. share-alike vs non-commercial), triggering column-level fallback
    """

    def __init__(self):
        self.hierarchy = LICENCE_HIERARCHY

    def get_ancestors(self, licence):
        """
        Return the full ancestor chain from a licence to the root of the hierarchy.
        e.g. cc_by_sa -> cc_by -> ogl -> any_licence
        """
        ancestors = []
        current = licence
        while current is not None:
            ancestors.append(current)
            current = self.hierarchy.get(current)
        return ancestors

    def _adds_incompatible_constraints(self, licence1, licence2):
        """
        Check if two licences add fundamentally incompatible constraint types (share-alike vs non-commercial vs database-share-alike). 
        When they do, no coherent single derived licence exists.
        """
        constraint_families = {
            "cc_by_sa":  "share_alike_document",
            "odbl":      "share_alike_database",
            "cc_by_nc":  "non_commercial",
        }

        f1 = constraint_families.get(licence1)
        f2 = constraint_families.get(licence2)

        # If both have distinct constraint families, they conflict
        if f1 and f2 and f1 != f2:
            return True
        return False

    def least_upper_bound(self, licence1, licence2):
        """
        Compute the least upper bound (LUB) of two licences.

        The LUB is the most specific common ancestor in the licence hierarchy - the least restrictive licence that is at least as restrictive
        as both inputs.

        Returns:
            {
                "derived_licence": str or "unknown", 
                "is_concrete": bool (False if abstract/unknown),
                "reasoning": str, 
                "fallback_to_column_level": bool
            }
        """
        # Same licence - trivial case
        if licence1 == licence2:
            return {
                "derived_licence": licence1,
                "is_concrete": True,
                "reasoning": (
                    f"Both inputs are {licence1}; "
                    f"derived licence is {licence1}"
                ),
                "fallback_to_column_level": False
            }

        # Check for incompatible constraint families
        # (share-alike vs non-commercial etc.)
        if self._adds_incompatible_constraints(licence1, licence2):
            return {
                "derived_licence": "unknown",
                "is_concrete": False,
                "reasoning": (
                    f"{licence1} and {licence2} add incompatible "
                    f"constraint types (e.g. share-alike vs "
                    f"non-commercial); no coherent single "
                    f"derived licence exists"
                ),
                "fallback_to_column_level": True
            }

        # Get ancestor chains
        ancestors1 = self.get_ancestors(licence1)
        ancestors2 = self.get_ancestors(licence2)

        # Check if one subsumes the other directly
        if licence1 in ancestors2:
            # licence1 is an ancestor of licence2
            # licence2 is more restrictive, so it dominates
            return {
                "derived_licence": licence2,
                "is_concrete": licence2 in LICENCE_DESCRIPTIONS,
                "reasoning": (
                    f"{licence2} subsumes {licence1}; "
                    f"derived licence is {licence2} "
                    f"(more restrictive)"
                ),
                "fallback_to_column_level": False
            }

        if licence2 in ancestors1:
            # licence2 is an ancestor of licence1
            return {
                "derived_licence": licence1,
                "is_concrete": licence1 in LICENCE_DESCRIPTIONS,
                "reasoning": (
                    f"{licence1} subsumes {licence2}; "
                    f"derived licence is {licence1} "
                    f"(more restrictive)"
                ),
                "fallback_to_column_level": False
            }

        # Find the first common ancestor (LUB)
        for ancestor in ancestors1:
            if ancestor in ancestors2:
                lub = ancestor
                # Check if the LUB is a concrete licence
                # or an abstract category
                is_abstract = lub in ["any_licence"]

                if is_abstract:
                    # No concrete derived licence exists
                    return {
                        "derived_licence": "unknown",
                        "is_concrete": False,
                        "reasoning": (
                            f"Least upper bound of {licence1} "
                            f"and {licence2} is the abstract "
                            f"category '{lub}'; no concrete "
                            f"derived licence exists"
                        ),
                        "fallback_to_column_level": True
                    }
                else:
                    return {
                        "derived_licence": lub,
                        "is_concrete": True,
                        "reasoning": (
                            f"Least upper bound of {licence1} "
                            f"and {licence2} is {lub}"
                        ),
                        "fallback_to_column_level": False
                    }

        # Should never reach here if hierarchy is complete
        return {
            "derived_licence": "unknown",
            "is_concrete": False,
            "reasoning": "No common ancestor found",
            "fallback_to_column_level": True
        }


# Integration with Column-Level Checker
# Implementation: use the ontology to compute the derived licence, and fall back to the column-level checker when the ontology returns "unknown".
# This connects the two main contributions of the dissertation (derived licence reasoning + column-level compliance) into a single coherent
# architecture.

def derive_licence_with_fallback(
    licence1, licence2,
    dataset1=None, dataset2=None
):
    """
    Integrated design for derived licence reasoning.

    Step 1: Query the licence ontology for the least upper bound of the two input licences.

    Step 2: If the ontology returns a concrete licence, return it as the derived dataset-level licence.

    Step 3: If the ontology returns "unknown" (no coherent single derived licence exists), signal that the system should fall back
     to the column-level compliance checker to salvage compliance at a finer granularity.

    This makes the connection between derived licence reasoning and column-level compliance explicit and architecturally principled, 
    rather than treating them as separate mechanisms.
    """
    ontology = LicenceOntology()
    result = ontology.least_upper_bound(licence1, licence2)

    if result["fallback_to_column_level"]:
        return {
            "approach": "column_level_required",
            "derived_licence": None,
            "message": (
                f"No coherent derived licence for {licence1} + "
                f"{licence2}. Ontology returned 'unknown'. "
                f"Column-level checker required to salvage "
                f"compliance at column granularity."
            ),
            "recommended_next_step": (
                f"Call ColumnLevelChecker.find_compliant_columns"
                f"({dataset1 or 'dataset1'}, "
                f"{dataset2 or 'dataset2'})"
            ),
            "ontology_reasoning": result["reasoning"]
        }

    return {
        "approach": "dataset_level",
        "derived_licence": result["derived_licence"],
        "message": (
            f"Derived licence for {licence1} + {licence2} "
            f"is {result['derived_licence']}"
        ),
        "recommended_next_step": (
            f"Proceed with dataset-level pipeline using "
            f"derived licence {result['derived_licence']}"
        ),
        "ontology_reasoning": result["reasoning"]
    }


# Demo
if __name__ == "__main__":
    ontology = LicenceOntology()

    print("=" * 65)
    print("LICENCE ONTOLOGY - LEAST UPPER BOUND REASONING")
    print("=" * 65)

    test_cases = [
        ("ogl", "ogl",
         "Same permissive licence"),
        ("cc_by_sa", "cc_by_sa",
         "Same share-alike licence"),
        ("ogl", "cc_by",
         "Two permissive licences"),
        ("ogl", "cc_by_sa",
         "Permissive + share-alike"),
        ("ogl", "cc_by_nc",
         "Permissive + non-commercial"),
        ("cc_by_sa", "odbl",
         "Two share-alikes (different families)"),
        ("cc_by_sa", "cc_by_nc",
         "Share-alike + non-commercial"),
        ("odbl", "cc_by_nc",
         "ODbL + non-commercial"),
    ]

    for l1, l2, description in test_cases:
        result = ontology.least_upper_bound(l1, l2)
        derived = result["derived_licence"]
        fallback = result["fallback_to_column_level"]

        print(f"\n{'-'*65}")
        print(f"  {description}")
        print(f"  {l1} + {l2}")
        print(f"  Derived licence: {derived}")
        print(f"  Reasoning: {result['reasoning']}")
        if fallback:
            print(f"  -> FALLBACK to column-level checker")
        else:
            print(f"  -> Concrete derived licence determined")

    # Summary
    print(f"\n{'='*65}")
    print("SUMMARY")
    print(f"{'='*65}")

    concrete = sum(
        1 for l1, l2, _ in test_cases
        if not ontology.least_upper_bound(l1, l2)[
            "fallback_to_column_level"
        ]
    )
    unknown = len(test_cases) - concrete

    print(f"  Concrete derived licence: {concrete}/{len(test_cases)}")
    print(f"  Unknown (column fallback): {unknown}/{len(test_cases)}")
    print(f"\n  Key insight: when the ontology cannot determine a concrete derived licence, the system falls back to column-level compliance checking - connecting the ")
    print(f"derived licence reasoning with the fine-grained column-level checker. ")
    print(f"{'='*65}")

    # Integrated Fallback Demo
    print(f"\n{'='*65}")
    print("INTEGRATED DEMO")
    print("Ontology query with column-level fallback")
    print(f"{'='*65}")

    integrated_cases = [
        ("ogl", "cc_by_sa",
         "air_quality", "met_office_weather",
         "Dataset-level derivation works"),
        ("cc_by_sa", "odbl",
         "met_office_weather", "osm_berkshire",
         "Fallback to column-level required"),
        ("cc_by_sa", "cc_by_nc",
         "met_office_weather", "nhs_admissions",
         "Incompatible constraint types"),
    ]

    for l1, l2, d1, d2, description in integrated_cases:
        print(f"\n  {description}")
        print(f"  Input: {d1}({l1}) + {d2}({l2})")

        result = derive_licence_with_fallback(l1, l2, d1, d2)

        print(f"  Approach: {result['approach']}")
        if result["derived_licence"]:
            print(f"  Derived licence: {result['derived_licence']}")
        print(f"  Recommendation: {result['recommended_next_step']}")

    print(f"\n{'='*65}")