# Data Analytics through Practical Reasoning for Decision Support

**MSc Data Science Dissertation - University of Bath**

**Author:** Rajveena Sahu
**Supervisor:** Prof. Julian Padget
**Academic Year:** 2025–2026

---

## Overview

This project develops a policy-aware data analytics pipeline management system. It detects licence violations when combining open datasets, automatically re-plans to find compliant alternatives, and extends compliance checking to the column level - preserving substantially more data than dataset-level approaches while maintaining full policy compliance.

The system uses:
- **ODRL 2.2** for machine-readable policy representation
- **Answer Set Programming (ASP)** via clingo for compliance reasoning
- **YAWL workflow patterns** for pipeline construction and re-planning

---

## Repository Structure

```
policies/          ODRL 2.2 Turtle policy files (4 licences)
asp/               ASP compliance rules (licence_rules.lp)
src/
  checker.py       Policy compliance checker (ASP/clingo)
  planner.py       YAWL-grounded pipeline planner with re-planning
  column_checker.py Column-level compliance checker (proof of concept)
  validate_odrl.py  rdflib validation of ODRL policy files
  create_synthetic_data.py  Generates synthetic NHS and Met Office datasets
data/              Real and synthetic datasets
evaluation/
  baseline.py      Static baseline pipeline (no policy checking)
  run_all.py       Three-way evaluation: dataset-level vs column-level vs baseline
  results.csv      Evaluation results
tests/
  test_checker.py           Unit tests for compliance checker (5 tests)
  test_planner.py           Integration tests for pipeline planner (8 tests)
  test_column_integration.py Column-level integration tests (2 tests)
```

---

## Licence Types Encoded

| Licence | ODRL File | Restrictiveness |
|---------|-----------|-----------------|
| OGL v3.0 | `policies/ogl_policy.ttl` | Least restrictive |
| CC-BY-NC 4.0 | `policies/cc_by_nc_policy.ttl` | Non-commercial only |
| CC-BY-SA 4.0 | `policies/cc_by_sa_policy.ttl` | Share-alike required |
| ODbL 1.0 | `policies/odbl_policy.ttl` | Derived database must remain open |

All policy files validated as well-formed RDF via rdflib. Cross-referenced against the rdflicense dataset, with vocabulary updated to ODRL 2.2.

---

## Evaluation Results

7 scenarios evaluated across 3 modes:

| Scenario | Dataset-Level | Column-Level | Baseline |
|----------|--------------|-------------|----------|
| Scenario 1 | Re-planned | 5/8 columns kept | Missed violation |
| Scenario 2 | Compliant | Compliant | Correct |
| Scenario 3 | Re-planned | 3/9 columns kept | Missed violation |
| Scenario 4 | Re-planned | 5/8 columns kept | Missed violation |
| Scenario 5 | Re-planned | Re-planned | Missed violation |
| Scenario 6 | CC-BY-SA preserved | CC-BY-SA preserved | Correct |
| Scenario 7 | Partial (no alternative) | Partial (no alternative) | Missed violation |

**Summary:**
- System: 7/7 licence-correct
- Column-level: saves data in 3 scenarios where dataset-level loses it
- Baseline: 2/7 correct, 5/7 violations missed silently

---

## How to Run

### Prerequisites
- Python 3.10+
- clingo (ASP solver)

### Setup
```bash
git clone https://github.com/Rajveena020/Msc_Dissertation.git
cd Msc_Dissertation
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\activate         # Windows
pip install clingo pandas numpy rdflib requests pytest
```

### Run the System
```bash
python src/validate_odrl.py          # Validate ODRL policy files
python src/planner.py                # Run all 7 scenarios
python src/column_checker.py         # Column-level compliance demo
python evaluation/run_all.py         # Full three-way evaluation
```

### Run Tests
```bash
python tests/test_checker.py              # 5 unit tests
python tests/test_planner.py              # 8 integration tests
python tests/test_column_integration.py   # 2 column-level tests
```

---

## Key Contribution

The column-level compliance checker demonstrates that policy compliance can be reasoned about at a finer grain than the dataset as a whole. In the NHS admissions example, dataset-level compliance excludes all 8 columns; column-level compliance identifies that only 3 columns cause the violation and preserves the remaining 5 - a 62.5% data preservation rate with identical policy compliance.

---

## Acknowledgements

- **Supervisor:** Prof. Julian Padget, University of Bath
- **ODRL Policy Cross-referencing:** rdflicense dataset (rdflicense.linkeddata.es)

---

## References

**BDI and Practical Reasoning:**
- De Silva, L., Meneguzzi, F. and Logan, B. (2020) 'BDI Agent Architectures: A Survey', *Proceedings of IJCAI-20*, pp. 4914-4921.
- Meneguzzi, F. and de Silva, L. (2015) 'Planning in BDI Agents: A Survey', *The Knowledge Engineering Review*, 30(1), pp. 1-44.
- Dung, P.M. (1995) 'On the Acceptability of Arguments', *Artificial Intelligence*, 77(2), pp. 321-357.
- Bench-Capon, T.J.M. and Dunne, P.E. (2007) 'Argumentation in Artificial Intelligence', *Artificial Intelligence*, 171(10-15), pp. 619-641.

**ASP and Policy Compliance:**
- Brewka, G., Eiter, T. and Truszczynski, M. (2011) 'Answer Set Programming at a Glance', *Communications of the ACM*, 54(12), pp. 92-103.
- Gebser, M. et al. (2012) *Answer Set Solving in Practice*. Morgan and Claypool Publishers.
- De Vos, M. et al. (2019) 'ODRL Policy Modelling and Compliance Checking', *RuleML+RR 2019*, LNCS 11784, pp. 36-51.
- Kampik, T. et al. (2022) 'Governance of Autonomous Agents on the Web', *ACM Transactions on Internet Technology*, 22(4), pp. 104:1-104:31.
- Padget, J. and Vasconcelos, W.W. (2018) 'Fine-Grained Access Control via Policy-Carrying Data', *ACM Transactions on Internet Technology*, 18(3), pp. 31:1-31:24.
- Bonatti, P.A. et al. (2020) 'Machine Understandable Policies and GDPR Compliance Checking', *KI - Künstliche Intelligenz*, 34(3), pp. 303-315.

**Machine-Readable Licence Formats:**
- W3C (2022) *ODRL Information Model 2.2*. Available at: https://www.w3.org/TR/odrl-model/
- Creative Commons (2023) *ccREL: The Creative Commons Rights Expression Language*. Available at: https://creativecommons.org/ns
- W3C (2020) *Data Catalog Vocabulary (DCAT) - Version 2*. Available at: https://www.w3.org/TR/vocab-dcat-2/
- Rodríguez-Doncel, V. et al. (2016) 'License Linked Data Resources', *Semantic Web*, 7(4), pp. 377-395.
- Dumontier, M. et al. (2024) 'Analysis of Ontologies and Policy Languages to Represent Information Flows in GDPR', *Semantic Web*.
- ISO/TC 46/SC 4 (2026) *DDI - Data Documentation Initiative*, ISO/PAS 25955:2026.

**Workflow Systems:**
- van der Aalst, W.M.P. and ter Hofstede, A.H.M. (2005) 'YAWL: Yet Another Workflow Language', *Information Systems*, 30(4), pp. 245-275.
- Munappy, A.R., Bosch, J. and Olsson, H.H. (2023) 'Data Pipeline Management in Practice', *Journal of Systems and Software*, 197, p. 111572.
- Deelman, E. et al. (2015) 'Pegasus, a Workflow Management System for Science Automation', *Future Generation Computer Systems*, 46, pp. 17-35.
- Sierhuis, M. (2001) *Modeling and Simulating Work Practice: BRAHMS*. PhD thesis, University of Amsterdam.

**Privacy and Consent:**
- Kirrane, S. et al. (2018) 'A Scalable Consent, Transparency and Compliance Architecture', *ESWC 2018 Satellite Events*, LNCS 11155, pp. 131–136.

**OPAL 2025 Workshop:**
- Cimmino, A. et al. (eds.) (2025) *1st International Workshop on ODRL and beyond (OPAL2025)*, CEUR Workshop Proceedings, Vol. 3977.
- Bonatti, P.A., Fornara, N. and Harth, A. (2025) 'Towards a Formal Semantics of ODRL 2.2', *OPAL 2025*, CEUR-WS Vol. 3977.
- Cimmino, A. and Fornara, N. (2025) 'Improving ODRL 2.2: Current Limitations and Theoretical Solutions', *OPAL 2025*, CEUR-WS Vol. 3977.
- Kieffer, M., Serrano-Alvarado, P. and Bernelin, M. (2025) 'Composing Complex Licenses to Facilitate Contextual Resources Reuse', *OPAL 2025*, CEUR-WS Vol. 3977.