import clingo

ctl = clingo.Control()
ctl.add("base", [], """
    dataset(air_quality).
    dataset(nhs_admissions).
    licence(air_quality, ogl).
    licence(nhs_admissions, cc_by_nc).

    violation :- licence(D1, ogl), 
                 licence(D2, cc_by_nc), 
                 combine(D1, D2).
    
    combine(air_quality, nhs_admissions).
""")

ctl.ground([("base", [])])

with ctl.solve(yield_=True) as handle:
    for model in handle:
        atoms = str(model)
        if "violation" in atoms:
            print("Policy violation detected!")
            print(f"Answer set: {atoms}")
        else:
            print("Pipeline is compliant.")
            