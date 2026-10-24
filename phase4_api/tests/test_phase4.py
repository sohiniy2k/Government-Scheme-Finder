"""Unit tests for Phase 4 Recommendation API using FastAPI TestClient."""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from phase4_api.main import app, recommendation_cache, schemes_list
from phase2_matching.matcher import MatchResults


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache_before_each_test():
    """Ensure in-memory cache is clean for every test."""
    recommendation_cache.clear()
    yield
    recommendation_cache.clear()


def make_valid_profile_payload(language: str = "en") -> dict:
    """Return valid profile payload for POST /api/recommend."""
    return {
        "age": 22,
        "state": "Maharashtra",
        "annual_income": 120000,
        "occupation": "student",
        "gender": "female",
        "social_category": "OBC",
        "disability": False,
        "bpl": "yes",
        "interests": ["Education & Learning"],
        "language": language,
    }


# =====================================================================
# 1. Health Endpoint Test
# =====================================================================

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["schemes_loaded"] > 0
    assert isinstance(data["groq_configured"], bool)

    # Security check: Ensure API key is NEVER exposed in response
    assert "GROQ_API_KEY" not in data
    assert "key" not in data
    assert not any(str(v).startswith("gsk_") for v in data.values())


# =====================================================================
# 2. Meta Endpoint Lists All 36 States & Metadata
# =====================================================================

def test_meta_endpoint_lists_all_36_states_and_categories():
    response = client.get("/api/meta")
    assert response.status_code == 200

    data = response.json()

    # Verify all 36 States/UTs
    states = data["states"]
    assert len(states) == 36
    assert "Maharashtra" in states
    assert "Goa" in states
    assert "Dadra and Nagar Haveli and Daman and Diu" in states
    assert "Jammu and Kashmir" in states

    # Verify 19 categories in interests
    interests = data["interests"]
    assert len(interests) == 19
    assert "Education & Learning" in interests
    assert "Agriculture" in interests

    # Verify other metadata lists
    assert "student" in data["occupations"]
    assert "female" in data["genders"]
    assert "SC" in data["social_categories"]
    assert "yes" in data["bpl"]
    assert data["languages"] == ["en", "hi"]


# =====================================================================
# 3. Recommend Happy Path Shape Test
# =====================================================================

@patch("phase4_api.main.explain")
def test_recommend_happy_path_shape(mock_explain):
    # Mock explainer returning top results with source="llm"
    def mock_explain_impl(matches, profile, top_n=5):
        return [
            {
                "id": m.scheme.id,
                "name": m.scheme.name,
                "level": m.scheme.level,
                "benefits": m.scheme.benefits,
                "official_url": m.scheme.official_url,
                "score": m.score,
                "summary": "Mocked simple summary.",
                "why_you_qualify": "Mocked why you qualify.",
                "things_to_check": ["Verify enrollment"],
                "documents_needed": ["Aadhaar card"],
                "how_to_apply": ["Step 1: Apply online"],
                "source": "llm",
            }
            for m in matches[:top_n]
        ]

    mock_explain.side_effect = mock_explain_impl

    payload = make_valid_profile_payload()
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "count" in data
    assert data["count"] > 0
    assert data["language"] == "en"
    assert "results" in data
    assert "more_schemes" in data
    assert "relaxation_hint" in data
    assert "disclaimer" in data

    # Verify results shape
    top_result = data["results"][0]
    expected_result_keys = {
        "id", "name", "level", "benefits", "official_url", "score",
        "summary", "why_you_qualify", "things_to_check", "documents_needed",
        "how_to_apply", "source"
    }
    assert expected_result_keys.issubset(top_result.keys())
    assert top_result["source"] == "llm"

    # Verify more_schemes shape (if present)
    if data["more_schemes"]:
        more_item = data["more_schemes"][0]
        expected_more_keys = {"id", "name", "level", "benefits", "official_url"}
        assert expected_more_keys.issubset(more_item.keys())
        assert len(more_item["benefits"]) <= 200


# =====================================================================
# 4. Invalid Age Returns 422
# =====================================================================

def test_invalid_age_returns_422():
    payload_negative = make_valid_profile_payload()
    payload_negative["age"] = -5
    res1 = client.post("/api/recommend", json=payload_negative)
    assert res1.status_code == 422

    payload_too_old = make_valid_profile_payload()
    payload_too_old["age"] = 150
    res2 = client.post("/api/recommend", json=payload_too_old)
    assert res2.status_code == 422


# =====================================================================
# 5. Zero Matches Returns Empty Results + Relaxation Hint
# =====================================================================

@patch("phase4_api.main.match")
def test_zero_matches_returns_empty_results_and_relaxation_hint(mock_match):
    # Simulate match engine returning 0 matches with a relaxation hint
    mock_match.return_value = MatchResults(
        [],
        relaxation_hint="4 schemes match if you ignore the income limit"
    )

    payload = make_valid_profile_payload()
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []
    assert data["more_schemes"] == []
    assert data["relaxation_hint"] == "4 schemes match if you ignore the income limit"
    assert "disclaimer" in data


# =====================================================================
# 6. Explainer Fallback Still Returns 200
# =====================================================================

@patch("phase4_api.main.explain")
def test_explainer_fallback_still_returns_200(mock_explain):
    # Simulate explainer returning fallback output (e.g. LLM timeout or error)
    def mock_explain_fallback(matches, profile, top_n=5):
        return [
            {
                "id": m.scheme.id,
                "name": m.scheme.name,
                "level": m.scheme.level,
                "benefits": m.scheme.benefits,
                "official_url": m.scheme.official_url,
                "score": m.score,
                "summary": "Fallback summary from template.",
                "why_you_qualify": "Fallback reasons.",
                "things_to_check": [],
                "documents_needed": [],
                "how_to_apply": ["Visit portal"],
                "source": "fallback",
            }
            for m in matches[:top_n]
        ]

    mock_explain.side_effect = mock_explain_fallback

    payload = make_valid_profile_payload()
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["count"] > 0
    assert data["results"][0]["source"] == "fallback"


# =====================================================================
# 7. Cache Hit Avoids Second Explainer Call
# =====================================================================

@patch("phase4_api.main.explain")
def test_cache_hit_avoids_second_explainer_call(mock_explain):
    mock_explain.return_value = [
        {
            "id": "cached-scheme-1",
            "name": "Cached Scheme",
            "level": "central",
            "benefits": "Benefits",
            "official_url": "https://gov.in",
            "score": 10,
            "summary": "Summary",
            "why_you_qualify": "Why",
            "things_to_check": [],
            "documents_needed": [],
            "how_to_apply": [],
            "source": "llm",
        }
    ]

    payload = make_valid_profile_payload()

    # First request: should call explainer and cache response
    res1 = client.post("/api/recommend", json=payload)
    assert res1.status_code == 200
    assert mock_explain.call_count == 1

    # Second request with identical payload: should hit cache and NOT call explainer
    res2 = client.post("/api/recommend", json=payload)
    assert res2.status_code == 200
    assert mock_explain.call_count == 1  # count remains 1!

    assert res1.json() == res2.json()


# =====================================================================
# 8. Scheme Endpoint by ID and 404
# =====================================================================

def test_scheme_endpoint_by_id_and_404():
    # 404 for non-existent scheme
    response_404 = client.get("/api/schemes/non-existent-scheme-slug-xyz")
    assert response_404.status_code == 404
    assert "not found" in response_404.json()["detail"].lower()

    # 200 for existing valid scheme
    first_scheme = schemes_list[0]
    response_200 = client.get(f"/api/schemes/{first_scheme.id}")
    assert response_200.status_code == 200

    scheme_data = response_200.json()
    assert scheme_data["id"] == first_scheme.id
    assert scheme_data["name"] == first_scheme.name
    assert "eligibility" in scheme_data
    assert "documents_required" in scheme_data
