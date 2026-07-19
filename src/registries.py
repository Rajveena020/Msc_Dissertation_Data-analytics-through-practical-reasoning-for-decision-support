# ============================================================
# registries.py
# Single Source of Truth for Licence Registries
# ============================================================


# Valid licence identifiers 
# These are the licence types the ASP rules and ontology understand. Passing a licence outside this set to the checker triggers an unknown_licence
# violation.

VALID_LICENCES = {
    "ogl",
    "cc_by",
    "cc_by_sa",
    "cc_by_nc",
    "odbl",
}


# Dataset-level licence assignments 
# Maps each dataset in the catalogue to its overall (dataset-level) licence. This is what the planner uses when reasoning about whole-dataset
# compliance.

DATASET_LICENCES = {
    "air_quality":        "ogl",
    "ons_census":         "ogl",
    "dft_traffic":        "ogl",
    "ons_health_stats":   "ogl",
    "defra_weather":      "ogl",
    "ons_geography":      "ogl",
    "ons_crime_stats":    "ogl",
    "police_crime":       "ogl",
    "nhs_admissions":     "cc_by_nc",
    "met_office_weather": "cc_by_sa",
    "osm_berkshire":      "odbl",
}


# Column-level licence registry 
# Maps each dataset to a dict of column -> licence, capturing the reality that many real datasets carry mixed licences at the column level
# even when the dataset as a whole is published under one licence.
#
# Two categories of dataset:
#   - MIXED: administrative columns are OGL but sensitive columns carry a restrictive licence
#   - UNIFORM: all columns carry the same licence as the dataset itself
#

COLUMN_REGISTRY = {
    # MIXED datasets
    "air_quality": {
        "date":     "ogl",
        "pm10":     "ogl",
        "no2":      "ogl",
        "o3":       "ogl",
        "region":   "ogl",
        "station":  "ogl",
    },

    "nhs_admissions": {
        # Administrative columns
        "admission_id":       "ogl",
        "hospital_code":      "ogl",
        "admission_date":     "ogl",
        "region":             "ogl",
        "admission_type":     "ogl",
        # Clinical columns are more restricted (CC-BY-NC)
        "diagnosis_code":     "cc_by_nc",
        "length_of_stay":     "cc_by_nc",
        "age_group":          "cc_by_nc",
    },

    "met_office_weather": {
        # Administrative columns
        "date":         "ogl",
        "station":      "ogl",
        "region":       "ogl",
        # Detailed meteorological data has CC-BY-SA constraint
        "temp_c":       "cc_by_sa",
        "rainfall_mm":  "cc_by_sa",
        "wind_speed":   "cc_by_sa",
        "humidity":     "cc_by_sa",
        "pressure":     "cc_by_sa",
        "visibility":   "cc_by_sa",
    },

    # UNIFORM datasets (all columns same licence) 
    "ons_census": {
        "record_id":       "ogl",
        "region":          "ogl",
        "population":      "ogl",
        "age_bracket":     "ogl",
        "household_size":  "ogl",
    },

    "police_crime": {
        "crime_id":     "ogl",
        "date":         "ogl",
        "region":       "ogl",
        "crime_type":   "ogl",
        "outcome":      "ogl",
    },

    "dft_traffic": {
        "record_id":       "ogl",
        "date":            "ogl",
        "road_type":       "ogl",
        "region":          "ogl",
        "vehicle_count":   "ogl",
        "average_speed":   "ogl",
    },

    "osm_berkshire": {
        "osm_id":       "odbl",
        "way_type":     "odbl",
        "geometry":     "odbl",
        "tags":         "odbl",
        "region":       "odbl",
    },

    "ons_health_stats": {
        "region":              "ogl",
        "hospital_code":       "ogl",
        "admission_count":     "ogl",
        "diagnosis_category":  "ogl",
        "age_group":           "ogl",
    },

    "defra_weather": {
        "date":         "ogl",
        "station":      "ogl",
        "region":       "ogl",
        "temp_c":       "ogl",
        "rainfall_mm":  "ogl",
    },

    "ons_geography": {
        "region":       "ogl",
        "boundary":     "ogl",
        "area_km2":     "ogl",
        "postcode":     "ogl",
    },

    "ons_crime_stats": {
        "region":       "ogl",
        "period":       "ogl",
        "crime_type":   "ogl",
        "count":        "ogl",
    },
}


# Licence restrictiveness ranking 
# Simplified linear ordering used by the "most-restrictive-wins" rule in derive_output_licence(). Intentionally coarse: CC-BY-SA and ODbL
# both carry rank 2 even though they impose share-alike on different scopes. The licence_ontology.py module provides the more principled
# multi-dimensional treatment.

LICENCE_RANK = {
    "ogl":      1,   # Attribution only
    "cc_by":    1,   # Attribution only
    "cc_by_sa": 2,   # Adds share-alike (document scope)
    "odbl":     2,   # Adds share-alike (database scope)
    "cc_by_nc": 3,   # Prohibits commercial use
}


# Domain-similar alternative datasets 
# When a dataset causes a violation, the re-planner consults this mapping to find candidate substitutions from the same subject domain
# but with a permissive licence.

DOMAIN_ALTERNATIVES = {
    "nhs_admissions":     ["ons_health_stats"],
    "met_office_weather": ["defra_weather"],
    "osm_berkshire":      ["ons_geography"],
    "police_crime":       ["ons_crime_stats"],
}


# Helper functions

def get_dataset_licence(dataset):
    """Return the licence of a whole dataset, or None if unknown."""
    return DATASET_LICENCES.get(dataset)


def get_column_licence(dataset, column):
    """Return the licence of a specific column, or None if unknown."""
    return COLUMN_REGISTRY.get(dataset, {}).get(column)


def get_all_columns(dataset):
    """Return all registered columns of a dataset."""
    return list(COLUMN_REGISTRY.get(dataset, {}).keys())


def get_licence_rank(licence):
    """Return the numeric restrictiveness rank of a licence."""
    return LICENCE_RANK.get(licence, 0)


def is_valid_licence(licence):
    """Return True if licence is recognised by the ASP rules."""
    return licence in VALID_LICENCES


def get_alternatives(dataset):
    """Return domain-similar alternatives for a dataset."""
    return DOMAIN_ALTERNATIVES.get(dataset, [])