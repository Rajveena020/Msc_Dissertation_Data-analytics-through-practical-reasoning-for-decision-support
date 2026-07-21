# MSc Dissertation - Data Analytics through Practical Reasoning for Decision Support

**Rajveena Sahu** | MSc Data Science | University of Bath | 2026
**Supervisor:** Prof. Julian Padget

---

## Overview

This dissertation builds a **policy-aware data analytics pipeline system** that detects licence conflicts between open datasets, automatically re-plans compliant alternatives, and reasons at the column level to preserve data that dataset-level approaches would discard.

The system combines:
- **ODRL 2.2** for machine-readable licence encoding (W3C Recommendation, hand-authored in Turtle)
- **Answer Set Programming (ASP)** via `clingo` for compliance reasoning
- **YAWL-grounded workflow patterns** for pipeline planning and re-planning
- **Column-level compliance checking** - the principal novel contribution

---

## Novel Contribution

**Column-level licence compliance.** Existing systems treat each dataset as carrying a single licence, so a licence conflict causes the entire dataset to be excluded from the pipeline. This system identifies which specific columns cause the violation and preserves the remainder.

**Example - Scenario 1** (`air_quality` OGL + `nhs_admissions` CC-BY-NC):
- Dataset-level compliance: excludes entire `nhs_admissions` dataset → 0/8 columns preserved
- Column-level compliance: excludes only the 3 CC-BY-NC clinical columns (`diagnosis_code`, `length_of_stay`, `age_group`) → **5/8 columns preserved (62.5%)**
- Output licence correctly derived from retained columns: **OGL**

To the best of my knowledge, no existing work integrates YAWL-grounded pipeline planning, ODRL 2.2 policy encoding, ASP-based compliance checking, and column-level fine-grained re-planning in a single system.

---

## Architecture

The system uses a **column-level-primary, dataset-substitution-fallback** strategy:

1. **Pre-pipeline policy check** - detects violations via ASP compliance rules
2. **If violation, column-level compliance is attempted first** - identifies compatible column subsets
3. **If column-level fails, dataset-level substitution is tried** - finds a domain-similar alternative
4. **If both fail, honest partial output is reported** - no false success (Objective O4)

### Repository Structure

```
policies/                          ODRL 2.2 Turtle policy files (4 licences)
asp/
  licence_rules.lp                 ASP compliance rules
src/
  registries.py                    Shared registries (datasets, columns, licences)
  checker.py                       Policy compliance checker (clingo symbol API)
  planner.py                       Pipeline planner (YAWL patterns + column-level primary)
  column_checker.py                Column-level compliance checker
  licence_ontology.py              OWL licence ontology (proof of concept)
  json_checker.py                  Non-tabular field-level checker (proof of concept)
evaluation/
  baseline.py                      Static pipeline without compliance checking
  run_all.py                       Evaluation harness - verified post-hoc
  results.csv                      Verified evaluation results
tests/                             19 unit and integration tests (all passing)
```

---

## ODRL 2.2 Policy Encodings

Four licences encoded manually in ODRL 2.2 Turtle format:

| Licence | Type | Key Constraints |
|---|---|---|
| OGL v3.0 | Open | Attribution required |
| CC-BY-NC 4.0 | Restricted | Non-commercial use only |
| CC-BY-SA 4.0 | Share-alike | Derivative must use same licence |
| ODbL 1.0 | Database | Derivative database must remain open |

All files validated as well-formed RDF via `rdflib`. Cross-referenced against the rdflicense catalogue where equivalents exist; vocabulary updated from ODRL 2.0 (rdflicense) to ODRL 2.2 (W3C Recommendation).

---

## Evaluation

Seven scenarios span the full space of licence combinations across 11 UK open datasets (real and synthetic). Results are **verified post-hoc** - each `licence_correct` claim is the output of running the compliance checker over the final pipeline datasets, not a hardcoded assertion.

| Scenario | Dataset-Level | Column-Level Primary | Baseline |
|---|---|---|---|
| Scenario 1 | Re-planned | **Col: 5/8 preserved** | Missed violation |
| Scenario 2 | Compliant | Compliant | Correct |
| Scenario 3 | Re-planned | **Col: 3/9 preserved** | Missed violation |
| Scenario 4 | Re-planned | **Col: 5/8 preserved** | Missed violation |
| Scenario 5 | Re-planned | Re-planned (col-level not viable) | Missed violation |
| Scenario 6 | CC-BY-SA preserved | CC-BY-SA preserved | Correct |
| Scenario 7 | Partial (O4) | Partial (O4) | Missed violation |

**Summary (verified post-hoc):**
- **Policy-aware system (dataset-level): 7/7 licence-correct** | 4 re-planned
- **Policy-aware system (column-level primary): 7/7 licence-correct** | 3 use column-level compliance
- **Static baseline: 2/7 correct** | 5 violations missed silently

Scenarios 4 and 7 correctly report "partial" when no compliant alternative exists - this is O4's success condition, not a failure of the reasoning apparatus.

---

## Tests

All 19 tests passing across four test suites:

| Test Suite | Tests | Coverage |
|---|---|---|
| `tests/test_checker.py` | 5 | ASP compliance checker unit tests |
| `tests/test_planner.py` | 8 | Pipeline planner integration tests |
| `tests/test_column_integration.py` | 2 | Column-level compliance end-to-end |
| `tests/test_json_integration.py` | 4 | JSON field-level checker end-to-end |

Run all tests:

```bash
python -m pytest tests/
```

Run a single suite:

```bash
python -m pytest tests/test_checker.py -v
```

---

## Reproducing the Evaluation

```bash
git clone https://github.com/Rajveena020/Msc_Dissertation_Data-analytics-through-practical-reasoning-for-decision-support
cd Msc_Dissertation_Data-analytics-through-practical-reasoning-for-decision-support
pip install -r requirements.txt

python evaluation/run_all.py
```

Results are written to `evaluation/results.csv` and printed to stdout.

---

## Dependencies

- Python 3.11+
- clingo 5.6+
- rdflib 6.3+
- pandas 2.0+

See `requirements.txt` for exact versions.

---

## Proof-of-Concept Extensions

Two extensions developed after the initial evaluation:

1. **`licence_ontology.py`** - OWL licence ontology with least-upper-bound computation over a licence lattice. Falls back to column-level checker when the ontology returns "unknown" for incompatible constraint combinations. Prompted by supervisory discussion of derived-licence semantics.

2. **`json_checker.py`** - Field-level compliance for nested JSON data using dot-notation paths. Preserves 9/13 fields (69%) in a representative patient-records + air-quality combination. Demonstrates that the column-level architecture generalises beyond tabular data.

---

## Bibliography Highlights

- **ODRL 2.2 formal semantics:** Bonatti, Fornara & Harth (OPAL 2025)
- **ODRL 2.2 limitations:** Cimmino & Fornara (OPAL 2025)
- **Licence composition:** Kieffer, Serrano-Alvarado & Bernelin (OPAL 2025)
- **Related ASP-ODRL compliance work:** De Vos, Kirrane, Padget & Satoh (RuleML+RR 2019)
- **Policy-carrying data:** Padget & Vasconcelos (ACM TOIT 2018)

Full bibliography in `references.bib`.

---

## Contact

**Rajveena Sahu** - rs3491@bath.ac.uk
Public repository: https://github.com/Rajveena020/Msc_Dissertation_Data-analytics-through-practical-reasoning-for-decision-support

