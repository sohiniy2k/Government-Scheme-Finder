"""Unit tests for Phase 3 LLM scheme explanation with mocked Groq calls."""

import os
import json
import pytest
from unittest.mock import patch
from phase1_data.schemas import Scheme, Eligibility
from phase2_matching.profile import UserProfile
from phase2_matching.matcher import SchemeMatch
from phase3_llm.prompts import prepare_prompt_payload, build_system_prompt, build_user_prompt
from phase3_llm.explainer import explain
from phase3_llm.groq_client import get_groq_api_key, get_groq_client


class MockGroqResponse:
    """Mock for Groq ChatCompletion choice/message response."""
    def __init__(self, content: str):
        self.choices = [
            type("Choice", (), {
                "message": type("Message", (), {"content": content})()
            })()
        ]


class MockGroqClient:
    """Mock Groq client avoiding any network calls."""
    def __init__(self, return_content: str = None, side_effect: Exception = None):
        self.return_content = return_content
        self.side_effect = side_effect
        self.last_kwargs = None
        self.chat = type("Chat", (), {
            "completions": type("Completions", (), {
                "create": self.create
            })()
        })()

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self.side_effect:
            raise self.side_effect
        return MockGroqResponse(self.return_content)


def make_test_match(
    id="pm-kisan",
    name="PM Kisan",
    level="central",
    benefits="Rs 6000 per year" * 60,  # 960 chars, exceeds 500
    docs=None,
    app_steps=None,
    match_reasons=None,
    unverified=None,
    score=10,
) -> SchemeMatch:
    """Helper to build fixture SchemeMatch instance."""
    documents_required = docs if docs is not None else [
        f"Doc {i}" for i in range(12)  # 12 docs, exceeds 8
    ]
    application_process = app_steps if app_steps is not None else [
        f"Step {i}" for i in range(8)   # 8 steps, exceeds 5
    ]
    scheme = Scheme(
        id=id,
        name=name,
        level=level,
        states=["ALL"],
        ministry="Ministry of Agriculture",
        category_tags=["Agriculture", "Income Support"],
        benefits=benefits,
        eligibility_text="Farmer with land",
        eligibility=Eligibility(
            min_age=18,
            max_age=None,
            genders=["any"],
            social_categories=["any"],
            max_annual_income=None,
            occupations=["farmer"],
            disability_required=False,
            bpl_required=False,
            other_conditions=["Must own land"],
        ),
        documents_required=documents_required,
        application_process=application_process,
        official_url=f"https://www.myscheme.gov.in/schemes/{id}",
        last_updated="2026-01-01",
    )
    return SchemeMatch(
        scheme=scheme,
        score=score,
        match_reasons=match_reasons if match_reasons is not None else ["Occupation matches: Farmer"],
        unverified_conditions=unverified if unverified is not None else ["Must own cultivable land"],
    )


def make_test_profile(language="en") -> UserProfile:
    """Helper to build test UserProfile."""
    return UserProfile(
        age=30,
        state="Maharashtra",
        annual_income=120000,
        occupation="farmer",
        gender="female",
        social_category="OBC",
        disability=False,
        bpl="no",
        interests=["Agriculture"],
        language=language,
    )


# =====================================================================
# 1. Prompt Contains Only Allowed Fields Test
# =====================================================================

def test_prompt_contains_only_allowed_fields_and_bounds():
    match_item = make_test_match()
    profile = make_test_profile()

    payload = prepare_prompt_payload([match_item], profile, top_n=5)
    schemes = payload["schemes"]
    assert len(schemes) == 1

    scheme_data = schemes[0]
    allowed_keys = {
        "id", "name", "level", "benefits", "match_reasons",
        "unverified_conditions", "documents_required", "application_process"
    }

    # Verify no disallowed keys exist in scheme payload
    assert set(scheme_data.keys()) == allowed_keys

    # Verify constraints: benefits <= 500 chars, docs <= 8, app_steps <= 5
    assert len(scheme_data["benefits"]) <= 500
    assert len(scheme_data["documents_required"]) <= 8
    assert len(scheme_data["application_process"]) <= 5

    # Verify citizen_profile has no personal identifiers
    citizen_profile = payload["citizen_profile"]
    disallowed_identifiers = {"name", "full_name", "first_name", "email", "phone", "aadhaar", "address"}
    for disallowed in disallowed_identifiers:
        assert disallowed not in citizen_profile


# =====================================================================
# 2. Valid JSON Parsed Test
# =====================================================================

def test_valid_json_parsed_successfully():
    match_item = make_test_match(
        id="pm-kisan",
        docs=["Aadhaar card", "Land records"],
        app_steps=["Step 1: Visit portal", "Step 2: Submit form"],
    )
    profile = make_test_profile()

    mock_llm_json = json.dumps({
        "results": [
            {
                "id": "pm-kisan",
                "summary": "Gives Rs 6,000 yearly to farmer families.",
                "why_you_qualify": "You are a registered farmer in Maharashtra.",
                "things_to_check": ["Ensure land title is updated"],
                "documents_needed": ["Aadhaar card", "Land records"],
                "how_to_apply": ["Step 1: Visit portal", "Step 2: Submit form"]
            }
        ]
    })
    mock_client = MockGroqClient(return_content=mock_llm_json)

    results = explain([match_item], profile, client=mock_client)
    assert len(results) == 1
    res = results[0]

    assert res["id"] == "pm-kisan"
    assert res["source"] == "llm"
    assert res["summary"] == "Gives Rs 6,000 yearly to farmer families."
    assert res["why_you_qualify"] == "You are a registered farmer in Maharashtra."
    assert res["things_to_check"] == ["Ensure land title is updated"]
    assert res["documents_needed"] == ["Aadhaar card", "Land records"]
    assert res["how_to_apply"] == ["Step 1: Visit portal", "Step 2: Submit form"]

    # Verify structured fields merged
    assert res["name"] == "PM Kisan"
    assert res["level"] == "central"
    assert res["score"] == 10
    assert "https://www.myscheme.gov.in/schemes/pm-kisan" in res["official_url"]


# =====================================================================
# 3. Hallucinated ID Dropped Test
# =====================================================================

def test_hallucinated_id_dropped():
    match_item = make_test_match(id="real-scheme")
    profile = make_test_profile()

    # LLM returns an invented id not in input
    mock_llm_json = json.dumps({
        "results": [
            {
                "id": "hallucinated-fake-id",
                "summary": "Invented free money scheme.",
                "why_you_qualify": "Everyone qualifies.",
                "things_to_check": [],
                "documents_needed": [],
                "how_to_apply": ["No apply needed"]
            }
        ]
    })
    mock_client = MockGroqClient(return_content=mock_llm_json)

    results = explain([match_item], profile, client=mock_client)
    assert len(results) == 1

    # Fake ID must NOT be present in output
    result_ids = [r["id"] for r in results]
    assert "hallucinated-fake-id" not in result_ids

    # Real scheme should be in output with fallback source
    assert results[0]["id"] == "real-scheme"
    assert results[0]["source"] == "fallback"


# =====================================================================
# 4. Document Count Mismatch Uses Original Docs Test
# =====================================================================

def test_document_count_mismatch_reverts_to_original():
    match_item = make_test_match(
        id="scheme-docs",
        docs=["Aadhaar card", "Bank passbook", "Land record"]  # 3 docs
    )
    profile = make_test_profile()

    # LLM only returns 1 document (mismatch: 1 != 3)
    mock_llm_json = json.dumps({
        "results": [
            {
                "id": "scheme-docs",
                "summary": "Support scheme.",
                "why_you_qualify": "You qualify.",
                "things_to_check": [],
                "documents_needed": ["Aadhaar card"],  # count mismatch!
                "how_to_apply": ["Step 1: Apply"]
            }
        ]
    })
    mock_client = MockGroqClient(return_content=mock_llm_json)

    results = explain([match_item], profile, client=mock_client)
    assert len(results) == 1

    # Explainer must detect count mismatch and revert to original 3 docs
    assert results[0]["documents_needed"] == ["Aadhaar card", "Bank passbook", "Land record"]
    assert results[0]["source"] == "llm"


# =====================================================================
# 5. Invalid JSON Triggers Fallback Test
# =====================================================================

def test_invalid_json_triggers_fallback():
    match_item = make_test_match(id="scheme-fallback-json")
    profile = make_test_profile()

    # LLM returns invalid JSON
    mock_client = MockGroqClient(return_content="Sorry, here is your answer: {not json")

    results = explain([match_item], profile, client=mock_client)
    assert len(results) == 1
    assert results[0]["id"] == "scheme-fallback-json"
    assert results[0]["source"] == "fallback"
    assert results[0]["summary"] is not None
    assert results[0]["why_you_qualify"] is not None


# =====================================================================
# 6. API Exception Triggers Fallback Test
# =====================================================================

def test_api_exception_triggers_fallback():
    match_item = make_test_match(id="scheme-api-err")
    profile = make_test_profile()

    # Mock client raises API error
    mock_client = MockGroqClient(side_effect=RuntimeError("Groq 500 Internal Server Error"))

    results = explain([match_item], profile, client=mock_client)
    assert len(results) == 1
    assert results[0]["id"] == "scheme-api-err"
    assert results[0]["source"] == "fallback"


# =====================================================================
# 7. Missing API Key Raises Clear Error Message Test
# =====================================================================

def test_missing_api_key_raises_clear_error():
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True):
        with pytest.raises(ValueError) as excinfo:
            get_groq_api_key()

        assert "GROQ_API_KEY" in str(excinfo.value)
        assert "not set" in str(excinfo.value).lower() or "missing" in str(excinfo.value).lower()

        with pytest.raises(ValueError) as excinfo_client:
            get_groq_client()
        assert "GROQ_API_KEY" in str(excinfo_client.value)
