%=============================================
%licence_rules.lp
% ASP Policy Compliance Rules
%=============================================

% Compatibility rules

% OGL + OGL = compatible
compatible(D1, D2) :-
    licence(D1, ogl),
    licence(D2, ogl).

% OGL + CC-BY = compatible
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

% ODbL + ODbL = compatible (same share-alike)
compatible(D1, D2) :-
    licence(D1, odbl),
    licence(D2, odbl).

% CC-BY-NC + CC-BY-NC = compatible (same non-commercial)
compatible(D1, D2) :-
    licence(D1, cc_by_nc),
    licence(D2, cc_by_nc).

% Violation rules 

% OGL + CC-BY-NC = violation (commercial restriction)
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

% OGL + ODbL = violation (open database requirement)
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

% General violation indicator 
violation_detected :- violation(_, _, _).

%  No violation = compliant 
compliant(D1, D2) :-
    combine(D1, D2),
    not violation(D1, D2, _).
    

% Machine-readable violation details 

% What rule was violated
violated_rule(D1, D2, commercial_use_prohibited) :-
    violation(D1, D2, cc_by_nc_restriction).

violated_rule(D1, D2, share_alike_required) :-
    violation(D1, D2, share_alike_conflict).

violated_rule(D1, D2, derived_db_must_be_open) :-
    violation(D1, D2, odbl_restriction).

violated_rule(D1, D2, nc_and_sa_incompatible) :-
    violation(D1, D2, nc_sa_conflict).

% What action caused the violation
violated_action(D1, D2, combine) :-
    violation(D1, D2, _).

% Which licence caused the violation
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
