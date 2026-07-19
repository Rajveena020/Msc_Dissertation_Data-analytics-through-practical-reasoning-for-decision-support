%=============================================
% licence_rules.lp
% ASP Policy Compliance Rules
%=============================================


%=============================================
% COMPATIBILITY RULES: Only pairs listed here are compliant.
%=============================================

% OGL + OGL = compatible
compatible(D1, D2) :-
    licence(D1, ogl),
    licence(D2, ogl).

% OGL + CC-BY = compatible (both directions)
compatible(D1, D2) :-
    licence(D1, ogl),
    licence(D2, cc_by).

compatible(D1, D2) :-
    licence(D1, cc_by),
    licence(D2, ogl).

% CC-BY + CC-BY = compatible
compatible(D1, D2) :-
    licence(D1, cc_by),
    licence(D2, cc_by).

% CC-BY-SA + CC-BY-SA = compatible (same share-alike)
compatible(D1, D2) :-
    licence(D1, cc_by_sa),
    licence(D2, cc_by_sa).

% ODbL + ODbL = compatible (same share-alike scope)
compatible(D1, D2) :-
    licence(D1, odbl),
    licence(D2, odbl).

% CC-BY-NC + CC-BY-NC = compatible (same non-commercial)
compatible(D1, D2) :-
    licence(D1, cc_by_nc),
    licence(D2, cc_by_nc).


%=============================================
% VIOLATION RULES: All violation rules declared symmetrically.
%=============================================

% OGL + CC-BY-NC = violation (commercial-use restriction)
violation(D1, D2, cc_by_nc_restriction) :-
    licence(D1, ogl),
    licence(D2, cc_by_nc),
    combine(D1, D2).

violation(D1, D2, cc_by_nc_restriction) :-
    licence(D1, cc_by_nc),
    licence(D2, ogl),
    combine(D1, D2).

% OGL + CC-BY-SA = violation (share-alike conflict)
violation(D1, D2, share_alike_conflict) :-
    licence(D1, ogl),
    licence(D2, cc_by_sa),
    combine(D1, D2).

violation(D1, D2, share_alike_conflict) :-
    licence(D1, cc_by_sa),
    licence(D2, ogl),
    combine(D1, D2).

% OGL + ODbL = violation (open-database requirement)
violation(D1, D2, odbl_restriction) :-
    licence(D1, ogl),
    licence(D2, odbl),
    combine(D1, D2).

violation(D1, D2, odbl_restriction) :-
    licence(D1, odbl),
    licence(D2, ogl),
    combine(D1, D2).

% CC-BY-NC + CC-BY-SA = violation
violation(D1, D2, nc_sa_conflict) :-
    licence(D1, cc_by_nc),
    licence(D2, cc_by_sa),
    combine(D1, D2).

violation(D1, D2, nc_sa_conflict) :-
    licence(D1, cc_by_sa),
    licence(D2, cc_by_nc),
    combine(D1, D2).

% CC-BY-SA + ODbL = violation (different share-alike scopes)
violation(D1, D2, sa_odbl_conflict) :-
    licence(D1, cc_by_sa),
    licence(D2, odbl),
    combine(D1, D2).

violation(D1, D2, sa_odbl_conflict) :-
    licence(D1, odbl),
    licence(D2, cc_by_sa),
    combine(D1, D2).

% CC-BY-NC + ODbL = violation (NC vs open-database conflict)
violation(D1, D2, nc_odbl_conflict) :-
    licence(D1, cc_by_nc),
    licence(D2, odbl),
    combine(D1, D2).

violation(D1, D2, nc_odbl_conflict) :-
    licence(D1, odbl),
    licence(D2, cc_by_nc),
    combine(D1, D2).


%=====================================================================
% UNKNOWN PAIR DETECTION: Any pair not explicitly compatible AND not 
% explicitly violating triggers unknown_pair violation.
%=====================================================================

violation(D1, D2, unknown_pair) :-
    combine(D1, D2),
    not compatible(D1, D2),
    not violation(D1, D2, cc_by_nc_restriction),
    not violation(D1, D2, share_alike_conflict),
    not violation(D1, D2, odbl_restriction),
    not violation(D1, D2, nc_sa_conflict),
    not violation(D1, D2, sa_odbl_conflict),
    not violation(D1, D2, nc_odbl_conflict).


%=============================================
% GENERAL VIOLATION INDICATOR
%=============================================

violation_detected :- violation(_, _, _).


%==================================================
% COMPLIANT = EXPLICITLY COMPATIBLE, NO VIOLATION
%==================================================

compliant(D1, D2) :-
    combine(D1, D2),
    compatible(D1, D2),
    not violation(D1, D2, _).


%=============================================
% MACHINE-READABLE VIOLATION DETAILS
%=============================================

% What rule was violated
violated_rule(D1, D2, commercial_use_prohibited) :-
    violation(D1, D2, cc_by_nc_restriction).

violated_rule(D1, D2, share_alike_required) :-
    violation(D1, D2, share_alike_conflict).

violated_rule(D1, D2, derived_db_must_be_open) :-
    violation(D1, D2, odbl_restriction).

violated_rule(D1, D2, nc_and_sa_incompatible) :-
    violation(D1, D2, nc_sa_conflict).

violated_rule(D1, D2, share_alike_scope_mismatch) :-
    violation(D1, D2, sa_odbl_conflict).

violated_rule(D1, D2, nc_and_odbl_incompatible) :-
    violation(D1, D2, nc_odbl_conflict).

violated_rule(D1, D2, no_compatibility_rule) :-
    violation(D1, D2, unknown_pair).

% What action caused the violation
violated_action(D1, D2, combine) :-
    violation(D1, D2, _).

% Which licence(s) caused the violation
violated_licence(D1, D2, L2) :-
    violation(D1, D2, _),
    licence(D2, L2).

violated_licence(D1, D2, L1) :-
    violation(D1, D2, _),
    licence(D1, L1).

% What constraint to add when re-planning
replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, cc_by_nc_restriction).

replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, share_alike_conflict).

replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, odbl_restriction).

replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, nc_sa_conflict).

replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, sa_odbl_conflict).

replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, nc_odbl_conflict).

replan_constraint(D1, D2, exclude(D2)) :-
    violation(D1, D2, unknown_pair).