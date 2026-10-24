"""Integration test calling live Groq API with 2 fixture schemes in English and Hindi."""

import os
from typing import List
import pytest
from dotenv import load_dotenv

from phase1_data.schemas import Scheme, Eligibility
from phase2_matching.profile import UserProfile
from phase2_matching.matcher import SchemeMatch
from phase3_llm.explainer import explain

# Load environment variables
load_dotenv()

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# Skip the entire module if GROQ_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not GROQ_KEY,
    reason="GROQ_API_KEY missing - skipping live Groq integration tests"
)


def make_fixture_matches() -> List[SchemeMatch]:
    """Create 2 fixture schemes for integration test."""
    scheme1 = Scheme(
        id="pm-kisan",
        name="Pradhan Mantri Kisan Samman Nidhi",
        level="central",
        states=["ALL"],
        ministry="Ministry of Agriculture",
        category_tags=["Agriculture", "Income Support"],
        benefits="Income support of Rs 6,000 per year in three equal installments to all landholding farmers.",
        eligibility_text="Small and marginal landholder farmer family.",
        eligibility=Eligibility(
            min_age=18,
            max_age=None,
            genders=["any"],
            social_categories=["any"],
            max_annual_income=None,
            occupations=["farmer"],
            disability_required=False,
            bpl_required=False,
            other_conditions=["Must own cultivable land"],
        ),
        documents_required=["Aadhaar card", "Land ownership documents", "Bank passbook"],
        application_process=[
            "Step 1: Visit official PM-KISAN portal",
            "Step 2: Enter Aadhaar number in Farmers Corner",
            "Step 3: Submit application and bank details"
        ],
        official_url="https://www.myscheme.gov.in/schemes/pm-kisan",
        last_updated=None,
    )
    match1 = SchemeMatch(
        scheme=scheme1,
        score=10,
        match_reasons=["Occupation matches: Farmer", "State-specific or central eligibility met"],
        unverified_conditions=["Must own cultivable land"],
    )

    scheme2 = Scheme(
        id="pm-awas",
        name="Pradhan Mantri Awaas Yojana - Gramin",
        level="central",
        states=["ALL"],
        ministry="Ministry of Rural Development",
        category_tags=["Housing & Shelter", "Social welfare & Empowerment"],
        benefits="Financial assistance of Rs 1,20,000 in plains and Rs 1,30,000 in hilly states for construction of pucca house.",
        eligibility_text="Families living in kutcha or dilapidated houses.",
        eligibility=Eligibility(
            min_age=18,
            max_age=None,
            genders=["any"],
            social_categories=["any"],
            max_annual_income=150000,
            occupations=["any"],
            disability_required=False,
            bpl_required=True,
            other_conditions=["Must not own a pucca house"],
        ),
        documents_required=["Aadhaar card", "BPL Ration Card", "Bank account details"],
        application_process=[
            "Step 1: Contact Gram Panchayat or Block Development Officer",
            "Step 2: Verify name in SECC priority list",
            "Step 3: Submit bank details for direct fund transfer"
        ],
        official_url="https://www.myscheme.gov.in/schemes/pm-awas",
        last_updated=None,
    )
    match2 = SchemeMatch(
        scheme=scheme2,
        score=8,
        match_reasons=["Income within eligibility", "BPL criteria matched"],
        unverified_conditions=["Must not own a pucca house"],
    )

    return [match1, match2]


def has_devanagari(text: str) -> bool:
    """Return True if text contains characters in the Unicode Devanagari range."""
    return any("\u0900" <= char <= "\u097F" for char in text)


def assert_valid_structure(res: dict, expected_id: str):
    """Assert result has valid shape, expected ID, and required keys."""
    required_keys = {
        "id", "name", "level", "benefits", "official_url", "score",
        "summary", "why_you_qualify", "things_to_check", "documents_needed",
        "how_to_apply", "source"
    }
    assert required_keys.issubset(res.keys())
    assert res["id"] == expected_id
    assert res["source"] == "llm"
    assert isinstance(res["summary"], str) and len(res["summary"]) > 0
    assert isinstance(res["why_you_qualify"], str) and len(res["why_you_qualify"]) > 0
    assert isinstance(res["things_to_check"], list)
    assert isinstance(res["documents_needed"], list)
    assert isinstance(res["how_to_apply"], list)


def test_real_groq_integration_english():
    matches = make_fixture_matches()
    profile_en = UserProfile(
        age=32,
        state="Uttar Pradesh",
        annual_income=80000,
        occupation="farmer",
        gender="male",
        social_category="General",
        disability=False,
        bpl="yes",
        interests=["Agriculture", "Housing & Shelter"],
        language="en",
    )

    results = explain(matches, profile_en, top_n=2)
    assert len(results) == 2

    input_ids = {"pm-kisan", "pm-awas"}
    returned_ids = {r["id"] for r in results}
    assert returned_ids == input_ids

    for r in results:
        assert_valid_structure(r, expected_id=r["id"])


def test_real_groq_integration_hindi():
    matches = make_fixture_matches()
    profile_hi = UserProfile(
        age=32,
        state="Uttar Pradesh",
        annual_income=80000,
        occupation="farmer",
        gender="male",
        social_category="General",
        disability=False,
        bpl="yes",
        interests=["Agriculture", "Housing & Shelter"],
        language="hi",
    )

    results = explain(matches, profile_hi, top_n=2)
    assert len(results) == 2

    input_ids = {"pm-kisan", "pm-awas"}
    returned_ids = {r["id"] for r in results}
    assert returned_ids == input_ids

    for r in results:
        assert_valid_structure(r, expected_id=r["id"])
        # Assert Hindi output contains Devanagari characters
        combined_text = f"{r['summary']} {r['why_you_qualify']}"
        assert has_devanagari(combined_text), (
            f"Expected Devanagari characters in Hindi output for scheme {r['id']}, got: {combined_text}"
        )
