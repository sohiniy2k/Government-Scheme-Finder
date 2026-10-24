"""Scoring module for ranking eligible schemes based on relevance and targeting."""

from typing import Tuple, List
from phase1_data.schemas import Scheme
from phase2_matching.profile import UserProfile


def score_scheme(profile: UserProfile, scheme: Scheme) -> Tuple[int, List[str]]:
    """
    Compute relevance score and plain-English match reasons for an eligible scheme.

    SCORING (higher = more targeted):
    +3 occupation specifically matched
    +3 per interest overlap (max 6)
    +2 gender matched (non-any)
    +2 category matched (non-any)
    +2 disability matched
    +1 age range matched
    +1 income limit matched
    +1 state-level scheme
    """
    score = 0
    reasons: List[str] = []

    # 1. Occupation specifically matched (+3)
    scheme_occs = [o.lower() for o in scheme.eligibility.occupations]
    if "any" not in scheme_occs and profile.occupation.lower() in scheme_occs:
        score += 3
        occ_display = profile.occupation.replace("_", " ").title()
        reasons.append(f"Occupation matches: {occ_display}")

    # 2. Interest overlap (+3 per overlap, max 6)
    if profile.interests:
        tag_set = {t.strip().lower() for t in scheme.category_tags}
        overlaps = [i for i in profile.interests if i.strip().lower() in tag_set]
        if overlaps:
            overlap_score = min(len(overlaps) * 3, 6)
            score += overlap_score
            reasons.append(f"Matches your interests in: {', '.join(overlaps[:2])}")

    # 3. Gender matched (non-any) (+2)
    scheme_genders = [g.lower() for g in scheme.eligibility.genders]
    if "any" not in scheme_genders and profile.gender != "prefer_not_to_say":
        if profile.gender.lower() in scheme_genders:
            score += 2
            reasons.append(f"Gender specifically matches: {profile.gender.title()}")

    # 4. Social category matched (non-any) (+2)
    scheme_cats = [c.lower() for c in scheme.eligibility.social_categories]
    if "any" not in scheme_cats and profile.social_category != "prefer_not_to_say":
        if profile.social_category.lower() in scheme_cats:
            score += 2
            reasons.append(f"Social category matches: {profile.social_category}")

    # 5. Disability matched (+2)
    if scheme.eligibility.disability_required and profile.disability:
        score += 2
        reasons.append("Provides dedicated benefits for persons with disability (Divyangjan)")

    # 6. Age range matched (+1)
    min_age = scheme.eligibility.min_age
    max_age = scheme.eligibility.max_age
    if min_age is not None and max_age is not None:
        score += 1
        reasons.append(f"Age {profile.age} is within {min_age}-{max_age} years")
    elif min_age is not None:
        score += 1
        reasons.append(f"Age {profile.age} meets minimum age of {min_age} years")
    elif max_age is not None:
        score += 1
        reasons.append(f"Age {profile.age} meets maximum age limit of {max_age} years")

    # 7. Income limit matched (+1)
    max_inc = scheme.eligibility.max_annual_income
    if max_inc is not None:
        score += 1
        reasons.append(f"Income ₹{profile.annual_income:,} is below the limit of ₹{max_inc:,}")

    # 8. State-level scheme (+1)
    if scheme.level.lower() == "state" or "ALL" not in scheme.states:
        score += 1
        reasons.append(f"State-specific scheme for {profile.state}")

    # Default fallback reason if no specific bonus matched
    if not reasons:
        reasons.append(f"Open central scheme available to residents of {profile.state}")

    return score, reasons
