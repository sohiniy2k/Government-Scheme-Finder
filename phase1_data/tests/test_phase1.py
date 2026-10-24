"""Unit tests for Phase 1 data parsing using fixture strings (not raw CSV)."""

import pytest
import pandas as pd
from pydantic import ValidationError
from phase1_data.parsers import (
    parse_money_amount,
    parse_income_from_sentence,
    parse_applicant_age,
    split_sentences,
    extract_states,
    parse_eligibility_data,
    extract_category_tags,
    extract_documents_required,
    extract_application_process,
)
from phase1_data.schemas import Scheme, Eligibility
from phase1_data.clean import process_schemes_dataframe


# =====================================================================
# 1. Money Parser Tests (6 formats + Rs. period handling + largest amount)
# =====================================================================

def test_money_parser_six_formats():
    # 1. "₹1,80,000/-"
    assert parse_money_amount("Family income must not exceed ₹1,80,000/- per annum.") == 180000

    # 2. "₹ 1,00,000"
    assert parse_money_amount("Annual income up to ₹ 1,00,000.") == 100000

    # 3. "Rs. 75000"
    assert parse_money_amount("Total household income Rs. 75000.") == 75000

    # 4. "2 lakh"
    assert parse_money_amount("Applicant income should be below 2 lakh.") == 200000

    # 5. "₹8 lakh"
    assert parse_money_amount("Annual family income limit is ₹8 lakh.") == 800000

    # 6. "1.5 lakh"
    assert parse_money_amount("Ceiling of 1.5 lakh per year.") == 150000


def test_money_parser_multiple_amounts_takes_largest():
    text = "Income limit is Rs. 50000 for rural and Rs. 1,00,000 for urban applicants."
    assert parse_money_amount(text) == 100000


def test_sentence_split_does_not_break_on_rs():
    text = "The annual income should not exceed Rs. 75000. The candidate must be a student."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert "Rs. 75000" in sentences[0]
    assert sentences[1] == "The candidate must be a student"


# =====================================================================
# 2. Age Parser Tests (5 patterns + 1 deceased case)
# =====================================================================

def test_age_parser_pattern1_x_to_y():
    # Pattern 1: "18 to 60 years"
    sentence = "The applicant age must be 18 to 60 years."
    min_age, max_age, is_applicant = parse_applicant_age(sentence)
    assert is_applicant is True
    assert min_age == 18
    assert max_age == 60


def test_age_parser_pattern2_hyphen():
    # Pattern 2: "18-60 years"
    sentence = "The candidate should be 18-60 years old."
    min_age, max_age, is_applicant = parse_applicant_age(sentence)
    assert is_applicant is True
    assert min_age == 18
    assert max_age == 60


def test_age_parser_pattern3_between_x_and_y():
    # Pattern 3: "between X and Y"
    sentence = "The student must be between 18 and 60 years of age."
    min_age, max_age, is_applicant = parse_applicant_age(sentence)
    assert is_applicant is True
    assert min_age == 18
    assert max_age == 60


def test_age_parser_pattern4_upper_bound():
    # Pattern 4: "under/below/less than X years"
    sentence = "The beneficiary should be below 35 years."
    min_age, max_age, is_applicant = parse_applicant_age(sentence)
    assert is_applicant is True
    assert min_age is None
    assert max_age == 35


def test_age_parser_pattern5_lower_bound():
    # Pattern 5: "above/at least/attained X years"
    sentence = "The applicant must be at least 21 years."
    min_age, max_age, is_applicant = parse_applicant_age(sentence)
    assert is_applicant is True
    assert min_age == 21
    assert max_age is None


def test_age_parser_deceased_case_goes_to_other_conditions():
    # Age sentence about deceased person should NOT set applicant min_age/max_age
    eligibility_text = "The deceased person should be between 18 and 60 years. Applicant must be a widow."
    elig = parse_eligibility_data(eligibility_text)
    assert elig.min_age is None
    assert elig.max_age is None
    assert any("deceased" in cond.lower() for cond in elig.other_conditions)


# =====================================================================
# 3. Goa vs Goat Test
# =====================================================================

def test_goa_vs_goat_word_boundary():
    # "goat" should not trigger Goa match
    goat_states = extract_states(
        level="state",
        scheme_name="Goat rearing and livestock development scheme",
        details="Provides financial support for goat farming.",
        eligibility="Must own at least 5 goats."
    )
    assert "Goa" not in goat_states
    assert goat_states == ["UNKNOWN"]

    # "Goa" with word boundary should trigger Goa match
    goa_states = extract_states(
        level="state",
        scheme_name="Fisheries Development Scheme in Goa",
        details="Subsidies for coastal fishermen.",
        eligibility="Must be a resident of the state."
    )
    assert goa_states == ["Goa"]


# =====================================================================
# 4. UT Aliases Tests
# =====================================================================

def test_ut_aliases_dadra_and_daman():
    # Daman alias
    states_daman = extract_states(
        level="state",
        scheme_name="Scholarship scheme for students in Daman",
        details="",
        eligibility=""
    )
    assert states_daman == ["Dadra and Nagar Haveli and Daman and Diu"]

    # Dadra alias
    states_dadra = extract_states(
        level="state",
        scheme_name="Welfare scheme in Dadra",
        details="",
        eligibility=""
    )
    assert states_dadra == ["Dadra and Nagar Haveli and Daman and Diu"]


def test_ut_aliases_jammu_and_jk():
    # Jammu alias
    states_jammu = extract_states(
        level="state",
        scheme_name="Healthcare initiative in Jammu",
        details="",
        eligibility=""
    )
    assert states_jammu == ["Jammu and Kashmir"]

    # J&K alias
    states_jk = extract_states(
        level="state",
        scheme_name="Youth empowerment scheme in J&K",
        details="",
        eligibility=""
    )
    assert states_jk == ["Jammu and Kashmir"]


# =====================================================================
# 5. Deduplication Test
# =====================================================================

def test_slug_deduplication():
    data = [
        {
            "slug": "pm-kisan",
            "scheme_name": "PM Kisan Version 1",
            "details": "Details 1",
            "benefits": "Benefits 1",
            "eligibility": "Applicant must be farmer.",
            "application": "Step 1: Apply online.",
            "documents": "Aadhaar card.",
            "level": "Central",
            "schemeCategory": "Agriculture",
            "tags": "farmer, kisan",
            "Unnamed: 9": "",
        },
        {
            "slug": "pm-kisan",
            "scheme_name": "PM Kisan Duplicate",
            "details": "Details 2",
            "benefits": "Benefits 2",
            "eligibility": "Applicant must be farmer.",
            "application": "Step 1: Apply online.",
            "documents": "Aadhaar card.",
            "level": "Central",
            "schemeCategory": "Agriculture",
            "tags": "farmer",
            "Unnamed: 9": "",
        },
        {
            "slug": "ayushman-bharat",
            "scheme_name": "Ayushman Bharat",
            "details": "Health coverage",
            "benefits": "5 lakh per family",
            "eligibility": "BPL family.",
            "application": "Step 1: Visit hospital.",
            "documents": "Ration card.",
            "level": "Central",
            "schemeCategory": "Health",
            "tags": "health",
            "Unnamed: 9": "",
        }
    ]
    df = pd.DataFrame(data)
    schemes = process_schemes_dataframe(df)

    assert len(schemes) == 2
    assert schemes[0].id == "pm-kisan"
    assert schemes[0].name == "PM Kisan Version 1"  # kept first
    assert schemes[1].id == "ayushman-bharat"


# =====================================================================
# 6. Pydantic Validation Tests
# =====================================================================

def test_pydantic_validation_success():
    scheme_dict = {
        "id": "test-scheme",
        "name": "Test Scheme for Girls in Goa",
        "level": "state",
        "states": ["Goa"],
        "ministry": None,
        "category_tags": ["Education", "Scholarship"],
        "benefits": "Financial aid of Rs 10000",
        "eligibility_text": "Applicant must be a female student between 18 and 25 years. Annual income must not exceed Rs. 1,00,000.",
        "eligibility": {
            "min_age": 18,
            "max_age": 25,
            "genders": ["female"],
            "social_categories": ["any"],
            "max_annual_income": 100000,
            "occupations": ["student"],
            "disability_required": False,
            "bpl_required": False,
            "other_conditions": []
        },
        "documents_required": ["Aadhaar card", "Marksheet"],
        "application_process": ["Register on portal", "Submit application"],
        "official_url": "https://www.myscheme.gov.in/schemes/test-scheme",
        "last_updated": None
    }
    scheme = Scheme.model_validate(scheme_dict)
    assert scheme.id == "test-scheme"
    assert scheme.eligibility.min_age == 18
    assert scheme.eligibility.genders == ["female"]
    assert scheme.eligibility.occupations == ["student"]
    assert scheme.eligibility.max_annual_income == 100000


def test_pydantic_validation_failure_on_invalid_types():
    with pytest.raises(ValidationError):
        Scheme.model_validate({
            "id": "missing-fields",
            # missing required fields like name, level, states, eligibility
        })

    with pytest.raises(ValidationError):
        Eligibility.model_validate({
            "min_age": "not-an-integer",  # Invalid type
        })
