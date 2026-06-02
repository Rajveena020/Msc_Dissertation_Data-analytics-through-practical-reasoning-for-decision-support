% ============================================================
% licence_rules.lp
% ASP Policy Compliance Rules
% Data Analytics through Practical Reasoning
% Rajveena Sahu | MSc Dissertation | University of Bath
% ============================================================

% ── Compatibility rules ──────────────────────────────────────

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

% ── Violation rules ──────────────────────────────────────────

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

% ── General violation indicator ──────────────────────────────
violation_detected :- violation(_, _, _).

% ── No violation = compliant ─────────────────────────────────
compliant(D1, D2) :-
    combine(D1, D2),
    not violation(D1, D2, _).

% ── Explanation helpers ──────────────────────────────────────
explanation(D1, D2, "CC-BY-NC prohibits commercial use - conflicts with OGL pipeline") :-
    violation(D1, D2, cc_by_nc_restriction).

explanation(D1, D2, "CC-BY-SA requires derived data to use same licence - conflicts with OGL") :-
    violation(D1, D2, share_alike_conflict).

explanation(D1, D2, "ODbL requires derived database to remain open - conflicts with OGL") :-
    violation(D1, D2, odbl_restriction).

explanation(D1, D2, "CC-BY-NC and CC-BY-SA are mutually incompatible") :-
    violation(D1, D2, nc_sa_conflict).