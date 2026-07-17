# ============================================================
# licence_ontology.py
# Licence Ontology with Lattice-Based Derived Licence Reasoning
# 
# PURPOSE:
# Implements Julian's suggestion of a licence ontology with formal hierarchy and least-upper-bound (LUB) queries for  computing the derived
# licence of combined datasets.
#
# Key insight: when the LUB query returns "unknown" (no coherent single derived licence exists), the system falls back to the column-level
# compliance checker - connecting the two main contributions of this dissertation.
#
# This is a simplified proof of concept. A production version would use OWL (Web Ontology Language) with a description logic reasoner 
# such as HermiT or Pellet.
# ============================================================

# Licence Lattice 
# Hierarchy from least restrictive (top) to most restrictive.
#
#                     any_licence
#                    /           \
#              permissive     restrictive
#              /    \          /       \
#           ogl   cc_by   share_alike  non_commercial
#                          /    \           |
#                     cc_by_sa  odbl     cc_by_nc
#
# Parent-child relationships encode: "child is at least as restrictive as parent." The least upper bound (LUB) of two licences is the most
# specific common ancestor - i.e., the least restrictive licence that is still at least as restrictive as both inputs.

LICENCE_HIERARCHY = {
    "ogl":            "permissive",
    "cc_by":          "permissive",
    "permissive":     "any_licence",
    "cc_by_sa":       "share_alike",
    "odbl":           "share_alike",
    "share_alike":    "restrictive",
    "cc_by_nc":       "non_commercial",
    "non_commercial": "restrictive",
    "restrictive":    "any_licence",
    "any_licence":    None,  # root
}

# Human-readable descriptions 
LICENCE_DESCRIPTIONS = {
    "ogl":            "Open Government Licence v3.0",
    "cc_by":          "Creative Commons Attribution 4.0",
    "cc_by_sa":       "Creative Commons Attribution-ShareAlike 4.0",
    "cc_by_nc":       "Creative Commons Attribution-NonCommercial 4.0",
    "odbl":           "Open Data Commons Open Database Licence 1.0",
    "permissive":     "(abstract) Permissive licence family",
    "share_alike":    "(abstract) Share-alike licence family",
    "non_commercial": "(abstract) Non-commercial licence family",
    "restrictive":    "(abstract) Restrictive licence family",
    "any_licence":    "(abstract) Root - any licence",
}


class LicenceOntology:
    """
    Licence ontology with least-upper-bound (LUB) queries.
    Given two licences, computes the derived licence for their combination using the formal lattice hierarchy.
    Returns:
    - A concrete licence if one subsumes the other "unknown" if no coherent derived licence exists (triggers column-level fallback)
    """

    def __init__(self):
        self.hierarchy = LICENCE_HIERARCHY

    def get_ancestors(self, licence):
        """
        Return the full ancestor chain from a licence to the root of the hierarchy.
        e.g. cc_by_sa -> share_alike -> restrictive -> any_licence
        """
        ancestors = []
        current = licence
        while current is not None:
            ancestors.append(current)
            current = self.hierarchy.get(current)
        return ancestors

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
                is_abstract = lub in [
                    "permissive", "restrictive",
                    "share_alike", "non_commercial",
                    "any_licence"
                ]

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
            print(f"  → FALLBACK to column-level checker")
        else:
            print(f"  → Concrete derived licence determined")

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
    print(f"\n  Key insight: When the ontology cannot determine a concrete derived licence, the system falls back to column-level compliance checking - connecting ")
    print(f" the derived licence reasoning with the fine-grained column-level checker. ")
    print(f"{'='*65}")