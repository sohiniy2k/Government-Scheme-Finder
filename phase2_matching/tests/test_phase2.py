"""Unit tests for Phase 2 User Profile and Matching Engine using fixture schemes."""

import pytest
from pydantic import ValidationError
from phase1_data.schemas import Scheme, Eligibility
from phase2_matching.profile import UserProfile
from phase2_matching.matcher import match, evaluate_hard_filters, get_relaxation_hint


def make_scheme(
    id="scheme-1",
    name="Test Scheme",
    level="central",
    states=None,
    min_age=None,
    max_age=None,
    genders=None,
    social_categories=None,
    max_annual_income=None,
    occupations=None,
    disability_required=False,
    bpl_required=False,
    category_tags=None,
    other_conditions=None,
) -> Scheme:
    """Helper to create fixture Scheme instances."""
    return Scheme(
        id=id,
        name=name,
        level=level,
        states=states if states is not None else ["ALL"],
        ministry=None,
        category_tags=category_tags if category_tags is not None else [],
        benefits="Sample benefits",
        eligibility_text="Sample eligibility text",
        eligibility=Eligibility(
            min_age=min_age,
            max_age=max_age,
            genders=genders if genders is not None else ["any"],
            social_categories=social_categories if social_categories is not None else ["any"],
            max_annual_income=max_annual_income,
            occupations=occupations if occupations is not None else ["any"],
            disability_required=disability_required,
            bpl_required=bpl_required,
            other_conditions=other_conditions if other_conditions is not None else [],
        ),
        documents_required=["Aadhaar card"],
        application_process=["Apply online"],
        official_url=f"https://www.myscheme.gov.in/schemes/{id}",
        last_updated=None,
    )


def make_profile(
    age=25,
    state="Maharashtra",
    annual_income=150000,
    occupation="student",
    gender="female",
    social_category="General",
    disability=False,
    bpl="no",
    interests=None,
    language="en",
) -> UserProfile:
    """Helper to create fixture UserProfile instances."""
    return UserProfile(
        age=age,
        state=state,
        annual_income=annual_income,
        occupation=occupation,
        gender=gender,
        social_category=social_category,
        disability=disability,
        bpl=bpl,
        interests=interests if interests is not None else [],
        language=language,
    )


# =====================================================================
# 1. Profile Validation Error Tests
# =====================================================================

def test_profile_validation_age_bounds():
    # Age < 0
    with pytest.raises(ValidationError):
        make_profile(age=-1)

    # Age > 120
    with pytest.raises(ValidationError):
        make_profile(age=125)


def test_profile_validation_negative_income():
    with pytest.raises(ValidationError):
        make_profile(annual_income=-500)


def test_profile_validation_invalid_state():
    with pytest.raises(ValidationError):
        make_profile(state="California")


def test_profile_validation_invalid_occupation():
    with pytest.raises(ValidationError):
        make_profile(occupation="astronaut")


def test_profile_validation_invalid_gender():
    with pytest.raises(ValidationError):
        make_profile(gender="unknown_gender")


def test_profile_validation_invalid_social_category():
    with pytest.raises(ValidationError):
        make_profile(social_category="Royalty")


def test_profile_validation_invalid_bpl():
    with pytest.raises(ValidationError):
        make_profile(bpl="maybe")


# =====================================================================
# 2. Hard Filters in Isolation Tests
# =====================================================================

def test_hard_filter_state_isolation():
    profile = make_profile(state="Karnataka")
    scheme_mh = make_scheme(level="state", states=["Maharashtra"])
    scheme_ka = make_scheme(level="state", states=["Karnataka"])

    assert evaluate_hard_filters(profile, scheme_mh)[0] is False
    assert evaluate_hard_filters(profile, scheme_ka)[0] is True


def test_hard_filter_age_isolation():
    profile_young = make_profile(age=16)
    profile_eligible = make_profile(age=22)
    profile_old = make_profile(age=45)

    scheme = make_scheme(min_age=18, max_age=35)

    assert evaluate_hard_filters(profile_young, scheme)[0] is False
    assert evaluate_hard_filters(profile_eligible, scheme)[0] is True
    assert evaluate_hard_filters(profile_old, scheme)[0] is False


def test_hard_filter_income_isolation():
    profile_rich = make_profile(annual_income=300000)
    profile_poor = make_profile(annual_income=150000)

    scheme = make_scheme(max_annual_income=200000)

    assert evaluate_hard_filters(profile_rich, scheme)[0] is False
    assert evaluate_hard_filters(profile_poor, scheme)[0] is True


def test_hard_filter_gender_isolation():
    scheme_female = make_scheme(genders=["female"])

    profile_male = make_profile(gender="male")
    profile_female = make_profile(gender="female")

    assert evaluate_hard_filters(profile_male, scheme_female)[0] is False
    assert evaluate_hard_filters(profile_female, scheme_female)[0] is True


def test_hard_filter_social_category_isolation():
    scheme_sc = make_scheme(social_categories=["SC"])

    profile_gen = make_profile(social_category="General")
    profile_sc = make_profile(social_category="SC")

    assert evaluate_hard_filters(profile_gen, scheme_sc)[0] is False
    assert evaluate_hard_filters(profile_sc, scheme_sc)[0] is True


def test_hard_filter_occupation_isolation():
    scheme_farmer = make_scheme(occupations=["farmer"])

    profile_student = make_profile(occupation="student")
    profile_farmer = make_profile(occupation="farmer")

    assert evaluate_hard_filters(profile_student, scheme_farmer)[0] is False
    assert evaluate_hard_filters(profile_farmer, scheme_farmer)[0] is True


def test_hard_filter_disability_isolation():
    scheme_pwd = make_scheme(disability_required=True)

    profile_no_disability = make_profile(disability=False)
    profile_with_disability = make_profile(disability=True)

    assert evaluate_hard_filters(profile_no_disability, scheme_pwd)[0] is False
    assert evaluate_hard_filters(profile_with_disability, scheme_pwd)[0] is True


def test_hard_filter_bpl_isolation():
    scheme_bpl = make_scheme(bpl_required=True)

    profile_bpl_no = make_profile(bpl="no")
    profile_bpl_yes = make_profile(bpl="yes")

    assert evaluate_hard_filters(profile_bpl_no, scheme_bpl)[0] is False
    assert evaluate_hard_filters(profile_bpl_yes, scheme_bpl)[0] is True


# =====================================================================
# 3. Central vs State Scheme Filtering
# =====================================================================

def test_central_shows_for_every_state_and_state_only_for_its_state():
    central_scheme = make_scheme(id="c1", level="central", states=["ALL"])
    goa_scheme = make_scheme(id="s1", level="state", states=["Goa"])

    profile_goa = make_profile(state="Goa")
    profile_bihar = make_profile(state="Bihar")

    schemes = [central_scheme, goa_scheme]

    # Goa user matches both
    matches_goa = match(profile_goa, schemes=schemes)
    assert len(matches_goa) == 2
    matched_ids_goa = {m.scheme.id for m in matches_goa}
    assert "c1" in matched_ids_goa
    assert "s1" in matched_ids_goa

    # Bihar user matches only central scheme
    matches_bihar = match(profile_bihar, schemes=schemes)
    assert len(matches_bihar) == 1
    assert matches_bihar[0].scheme.id == "c1"


# =====================================================================
# 4. UNKNOWN State Excluded Test
# =====================================================================

def test_unknown_state_scheme_is_excluded():
    unknown_scheme = make_scheme(level="state", states=["UNKNOWN"])
    profile = make_profile(state="Maharashtra")

    assert evaluate_hard_filters(profile, unknown_scheme)[0] is False
    results = match(profile, schemes=[unknown_scheme])
    assert len(results) == 0


# =====================================================================
# 5. prefer_not_to_say / unknown Keeps Scheme with Unverified Check
# =====================================================================

def test_prefer_not_to_say_gender_keeps_scheme_with_check():
    scheme_female = make_scheme(
        id="f1",
        genders=["female"],
        other_conditions=["Must be enrolled in college"]
    )
    profile = make_profile(gender="prefer_not_to_say")

    passed, unverified_checks = evaluate_hard_filters(profile, scheme_female)
    assert passed is True
    assert any("Gender requirement" in check for check in unverified_checks)

    results = match(profile, schemes=[scheme_female])
    assert len(results) == 1
    assert any("Gender requirement" in cond for cond in results[0].unverified_conditions)


def test_prefer_not_to_say_category_keeps_scheme_with_check():
    scheme_sc = make_scheme(
        id="sc1",
        social_categories=["SC"],
        other_conditions=["Original caste certificate required"]
    )
    profile = make_profile(social_category="prefer_not_to_say")

    passed, unverified_checks = evaluate_hard_filters(profile, scheme_sc)
    assert passed is True
    assert any("Category requirement" in check for check in unverified_checks)

    results = match(profile, schemes=[scheme_sc])
    assert len(results) == 1
    assert any("Category requirement" in cond for cond in results[0].unverified_conditions)


def test_unknown_bpl_keeps_scheme_with_check():
    scheme_bpl = make_scheme(id="bpl1", bpl_required=True)
    profile = make_profile(bpl="unknown")

    passed, unverified_checks = evaluate_hard_filters(profile, scheme_bpl)
    assert passed is True
    assert any("BPL status" in check for check in unverified_checks)

    results = match(profile, schemes=[scheme_bpl])
    assert len(results) == 1
    assert any("BPL status" in cond for cond in results[0].unverified_conditions)


# =====================================================================
# 6. Scoring and Ranking Order Tests
# =====================================================================

def test_scoring_order_and_points():
    profile = make_profile(
        age=22,
        state="Kerala",
        annual_income=120000,
        occupation="farmer",
        gender="female",
        social_category="SC",
        disability=True,
        bpl="yes",
        interests=["Agriculture", "Education"],
    )

    # Scheme A: highly targeted (+3 occupation, +6 interests, +2 gender, +2 category, +2 disability, +1 age, +1 income, +1 state)
    scheme_targeted = make_scheme(
        id="targeted",
        name="Kerala Targeted Farmer Scheme",
        level="state",
        states=["Kerala"],
        occupations=["farmer"],
        category_tags=["Agriculture", "Education"],
        genders=["female"],
        social_categories=["SC"],
        disability_required=True,
        min_age=18,
        max_age=35,
        max_annual_income=200000,
    )

    # Scheme B: general central scheme (+1 income, +1 age, no specific bonuses)
    scheme_general = make_scheme(
        id="general",
        name="National General Welfare",
        level="central",
        states=["ALL"],
        min_age=18,
        max_age=60,
        max_annual_income=200000,
    )

    schemes = [scheme_general, scheme_targeted]
    results = match(profile, schemes=schemes)

    assert len(results) == 2
    # Targeted scheme must be ranked first with a significantly higher score
    assert results[0].scheme.id == "targeted"
    assert results[0].score > results[1].score
    # Expected targeted score = 3 (occ) + 6 (interests) + 2 (gender) + 2 (category) + 2 (disability) + 1 (age) + 1 (income) + 1 (state) = 18
    assert results[0].score == 18


def test_scoring_tie_break_state_before_central_then_alphabetical():
    profile = make_profile(state="Tamil Nadu")

    # Three schemes with identical score 0 (open central/state, all defaults)
    scheme_central = make_scheme(id="c1", name="Central Beta", level="central", states=["ALL"])
    scheme_state_z = make_scheme(id="s1", name="Tamil Nadu Zebra", level="state", states=["Tamil Nadu"])
    scheme_state_a = make_scheme(id="s2", name="Tamil Nadu Alpha", level="state", states=["Tamil Nadu"])

    # All match Tamil Nadu user. State schemes get +1 for state bonus.
    # To test tie-break on equal score, give all 3 the same level bonus or compare between states:
    # scheme_state_a and scheme_state_z both get score=1 (state bonus).
    # scheme_state_a ("Tamil Nadu Alpha") should come before scheme_state_z ("Tamil Nadu Zebra").
    results = match(profile, schemes=[scheme_state_z, scheme_state_a, scheme_central])

    assert len(results) == 3
    # Top 2 are state schemes (score 1 vs central score 0)
    assert results[0].scheme.id == "s2"  # Tamil Nadu Alpha
    assert results[1].scheme.id == "s1"  # Tamil Nadu Zebra
    assert results[2].scheme.id == "c1"  # Central Beta


# =====================================================================
# 7. Relaxation Hint when 0 Matches
# =====================================================================

def test_relaxation_hint_income():
    # User income is 500,000, but schemes have limit 200,000
    profile = make_profile(annual_income=500000)
    schemes = [
        make_scheme(id="s1", max_annual_income=200000),
        make_scheme(id="s2", max_annual_income=250000),
    ]

    results = match(profile, schemes=schemes)
    assert len(results) == 0
    assert results.relaxation_hint is not None
    assert "income limit" in results.relaxation_hint
    assert "2 schemes match" in results.relaxation_hint


def test_relaxation_hint_age():
    # User age is 70, but scheme is for 18-35
    profile = make_profile(age=70)
    scheme = make_scheme(min_age=18, max_age=35)

    hint = get_relaxation_hint(profile, [scheme])
    assert hint is not None
    assert "age requirement" in hint
    assert "1 scheme matches" in hint
