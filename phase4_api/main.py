"""FastAPI service exposing Phase 1-3 recommendation pipeline."""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from phase1_data.constants import STATES_AND_UTS
from phase2_matching.profile import UserProfile, PROFILE_OCCUPATIONS
from phase2_matching.loader import load_schemes, get_categories
from phase2_matching.matcher import match
from phase3_llm.explainer import explain
from phase4_api.cache import RecommendationCache

# Load environment configuration
load_dotenv()

DISCLAIMER_TEXT = (
    "This service helps you discover government schemes you may be eligible for, "
    "but does not guarantee eligibility or submit applications. Final eligibility "
    "is determined by the relevant government department."
)

# Initialize application
app = FastAPI(
    title="Government Scheme Finder API",
    description="Deterministic matching and plain-language LLM explanations for Indian government schemes.",
    version="1.0.0",
)

# CORS middleware
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load schemes once at startup
schemes_list = load_schemes()
schemes_by_id = {s.id: s for s in schemes_list}
available_categories = get_categories(schemes_list)

# In-memory recommendation cache
recommendation_cache = RecommendationCache(max_size=200, ttl_seconds=3600)


@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check reporting schemes count and Groq configuration status."""
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    return {
        "status": "ok",
        "schemes_loaded": len(schemes_list),
        "groq_configured": bool(groq_key),
    }


@app.get("/api/meta")
def get_meta() -> Dict[str, Any]:
    """Dropdown metadata options for profile form construction."""
    return {
        "states": STATES_AND_UTS,
        "occupations": PROFILE_OCCUPATIONS,
        "genders": ["male", "female", "transgender", "prefer_not_to_say"],
        "social_categories": ["General", "SC", "ST", "OBC", "EWS", "Minority", "prefer_not_to_say"],
        "bpl": ["yes", "no", "unknown"],
        "interests": available_categories,
        "languages": ["en", "hi"],
    }


@app.post("/api/recommend")
def recommend_schemes(profile: UserProfile) -> Dict[str, Any]:
    """
    Recommend matching schemes for user profile.
    Top 5 explained via LLM, next 5 returned as more_schemes.
    Cached if all results are from LLM.
    """
    profile_dict = profile.model_dump()
    cache_key = recommendation_cache.compute_key(profile_dict)

    # Check cache hit
    cached_data = recommendation_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Match candidate schemes
    matches = match(profile, schemes=schemes_list, top_n=10)

    if not matches:
        return {
            "count": 0,
            "language": profile.language,
            "results": [],
            "more_schemes": [],
            "relaxation_hint": matches.relaxation_hint,
            "disclaimer": DISCLAIMER_TEXT,
        }

    # Top 5 explained via Phase 3
    top_matches = matches[:5]
    explained_results = explain(top_matches, profile, top_n=5)

    # Next 5 as more_schemes (structured preview only, no LLM call)
    more_matches = matches[5:10]
    more_schemes = [
        {
            "id": m.scheme.id,
            "name": m.scheme.name,
            "level": m.scheme.level,
            "benefits": (m.scheme.benefits or "").strip()[:200],
            "official_url": m.scheme.official_url,
        }
        for m in more_matches
    ]

    # Dedupe by scheme id
    seen_ids = set()
    deduped_results = []
    for res in explained_results:
        if res["id"] not in seen_ids:
            seen_ids.add(res["id"])
            deduped_results.append(res)

    deduped_more = []
    for more in more_schemes:
        if more["id"] not in seen_ids:
            seen_ids.add(more["id"])
            deduped_more.append(more)

    response_payload = {
        "count": len(deduped_results),
        "language": profile.language,
        "results": deduped_results,
        "more_schemes": deduped_more,
        "relaxation_hint": matches.relaxation_hint,
        "disclaimer": DISCLAIMER_TEXT,
    }

    # Only cache responses where every result has source="llm"
    if deduped_results and all(r.get("source") == "llm" for r in deduped_results):
        recommendation_cache.set(cache_key, response_payload)

    return response_payload


@app.get("/api/schemes/{id}")
def get_scheme_by_id(id: str) -> Dict[str, Any]:
    """Retrieve full scheme record by slug id."""
    scheme = schemes_by_id.get(id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{id}' not found")
    return scheme.model_dump()
