"""Hard filtering, matching engine, and no-results relaxation handling."""

from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel
from phase1_data.schemas import Scheme
from phase2_matching.profile import UserProfile
from phase2_matching.loader import load_schemes
from phase2_matching.scorer import score_scheme


class SchemeMatch(BaseModel):
    scheme: Scheme
    score: int
    match_reasons: List[str]
    unverified_conditions: List[str]

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class MatchResults(list):
    """Subclass of list holding SchemeMatch items with an optional relaxation_hint attribute."""
    def __init__(self, items=(), relaxation_hint: Optional[str] = None):
        super().__init__(items)
        self.relaxation_hint = relaxation_hint


def evaluate_hard_filters(
    profile: UserProfile,
    scheme: Scheme,
    relax_filter: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Evaluates hard filters on a scheme against the user profile.
    Exclude scheme if any filter fails (null = no restriction).

    Filters:
    - state: scheme states has 'ALL' or user's state. Exclude 'UNKNOWN'.
    - age: within min_age/max_age.
    - income: annual_income <= max_annual_income.
    - gender: scheme ['any'] or includes user gender.
    - social_categories: ['any'] or includes user category.
    - occupations: ['any'] or includes user occupation.
    - disability_required: true -> user must have disability.
    - bpl_required: true -> exclude if bpl 'no'.
    - 'prefer_not_to_say'/'unknown': do not exclude; add to unverified_conditions instead.

    relax_filter: optional name of filter to bypass ('income', 'age', 'occupation', 'social_category').
    """
    unverified_checks: List[str] = []

    # 1. State filter
    # Exclude UNKNOWN
    if "UNKNOWN" in scheme.states or scheme.states == ["UNKNOWN"]:
        return False, []
    # Scheme is applicable if 'ALL' or user state is present
    if "ALL" not in scheme.states and profile.state not in scheme.states:
        return False, []

    # 2. Age filter
    if relax_filter != "age":
        min_age = scheme.eligibility.min_age
        max_age = scheme.eligibility.max_age
        if min_age is not None and profile.age < min_age:
            return False, []
        if max_age is not None and profile.age > max_age:
            return False, []

    # 3. Income filter
    if relax_filter != "income":
        max_inc = scheme.eligibility.max_annual_income
        if max_inc is not None and profile.annual_income > max_inc:
            return False, []

    # 4. Gender filter
    scheme_genders = [g.lower() for g in scheme.eligibility.genders]
    if "any" not in scheme_genders:
        if profile.gender == "prefer_not_to_say":
            unverified_checks.append(
                f"Gender requirement: Scheme specifies {', '.join(scheme.eligibility.genders)} (not verified)"
            )
        elif profile.gender.lower() not in scheme_genders:
            return False, []

    # 5. Social categories filter
    if relax_filter != "social_category":
        scheme_cats = [c.lower() for c in scheme.eligibility.social_categories]
        if "any" not in scheme_cats:
            if profile.social_category == "prefer_not_to_say":
                unverified_checks.append(
                    f"Category requirement: Scheme specifies {', '.join(scheme.eligibility.social_categories)} (not verified)"
                )
            elif profile.social_category.lower() not in scheme_cats:
                return False, []

    # 6. Occupation filter
    if relax_filter != "occupation":
        scheme_occs = [o.lower() for o in scheme.eligibility.occupations]
        if "any" not in scheme_occs:
            if profile.occupation.lower() not in scheme_occs:
                return False, []

    # 7. Disability filter
    if scheme.eligibility.disability_required and not profile.disability:
        return False, []

    # 8. BPL filter
    if scheme.eligibility.bpl_required:
        if profile.bpl == "no":
            return False, []
        elif profile.bpl == "unknown":
            unverified_checks.append(
                "BPL status: Scheme requires Below Poverty Line (BPL) status (not verified)"
            )

    return True, unverified_checks


def get_relaxation_hint(profile: UserProfile, schemes: List[Scheme]) -> Optional[str]:
    """
    If 0 matches, relax each of income, age, occupation, social_category one at a time
    and return relaxation hint.
    """
    filters_to_relax = [
        ("income", "income limit"),
        ("age", "age requirement"),
        ("occupation", "occupation requirement"),
        ("social_category", "category requirement"),
    ]

    relaxation_results = []
    for filter_key, display_name in filters_to_relax:
        count = sum(
            1 for s in schemes
            if evaluate_hard_filters(profile, s, relax_filter=filter_key)[0]
        )
        if count > 0:
            relaxation_results.append((count, filter_key, display_name))

    if not relaxation_results:
        return None

    # Pick the relaxation that yields the most matching schemes
    relaxation_results.sort(key=lambda x: x[0], reverse=True)
    best_count, _, best_name = relaxation_results[0]
    plural_scheme = "schemes match" if best_count != 1 else "scheme matches"
    return f"{best_count} {plural_scheme} if you ignore the {best_name}"


def match(
    profile: UserProfile,
    schemes: Optional[List[Scheme]] = None,
    top_n: int = 10
) -> MatchResults:
    """
    Match user profile deterministically against candidate schemes.

    1. Evaluates hard filters.
    2. If 0 matches, computes relaxation hint.
    3. If matches found, scores each scheme and sorts:
       - score descending
       - state before central
       - scheme name ascending
    4. Attaches match reasons and unverified conditions (other_conditions[:3] + checks).
    """
    if schemes is None:
        schemes = load_schemes()

    eligible_items = []
    for s in schemes:
        passed, unverified_checks = evaluate_hard_filters(profile, s)
        if passed:
            score, reasons = score_scheme(profile, s)
            unverified = s.eligibility.other_conditions[:3] + unverified_checks
            eligible_items.append(
                SchemeMatch(
                    scheme=s,
                    score=score,
                    match_reasons=reasons,
                    unverified_conditions=unverified,
                )
            )

    if not eligible_items:
        hint = get_relaxation_hint(profile, schemes)
        return MatchResults([], relaxation_hint=hint)

    # Sort: higher score first, state before central, name alphabetical
    eligible_items.sort(
        key=lambda m: (
            -m.score,
            0 if m.scheme.level.lower() == "state" else 1,
            m.scheme.name.lower()
        )
    )

    return MatchResults(eligible_items[:top_n], relaxation_hint=None)
