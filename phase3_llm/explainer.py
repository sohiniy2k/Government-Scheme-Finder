"""Explainer module turning matched scheme data into plain-language explanations."""

import json
from typing import List, Dict, Any, Optional
from phase2_matching.profile import UserProfile
from phase2_matching.matcher import SchemeMatch
from phase3_llm.groq_client import call_groq
from phase3_llm.prompts import build_system_prompt, build_user_prompt


def build_fallback_explanation(m: SchemeMatch, profile: UserProfile) -> Dict[str, Any]:
    """
    Template explanation built from match_reasons, unverified_conditions,
    documents_required, and application_process.
    """
    scheme = m.scheme
    benefits_excerpt = (scheme.benefits or "").strip()
    if len(benefits_excerpt) > 200:
        benefits_excerpt = benefits_excerpt[:200] + "..."

    summary = (
        f"{scheme.name} is a {scheme.level} scheme offering {benefits_excerpt or 'welfare benefits for eligible applicants'}."
    )

    why_you_qualify = (
        ". ".join(m.match_reasons) + "."
        if m.match_reasons
        else "You meet the demographic and eligibility criteria for this scheme."
    )

    things_to_check = list(m.unverified_conditions) if m.unverified_conditions else []
    docs_needed = list(scheme.documents_required[:8]) if scheme.documents_required else []
    how_to_apply = list(scheme.application_process[:5]) if scheme.application_process else [
        "Apply online through the official portal or visit the nearest citizen service center."
    ]

    return {
        "id": scheme.id,
        "name": scheme.name,
        "level": scheme.level,
        "benefits": scheme.benefits,
        "official_url": scheme.official_url,
        "score": m.score,
        "summary": summary,
        "why_you_qualify": why_you_qualify,
        "things_to_check": things_to_check,
        "documents_needed": docs_needed,
        "how_to_apply": how_to_apply,
        "source": "fallback",
    }


def explain(
    matches: List[SchemeMatch],
    profile: UserProfile,
    top_n: int = 5,
    client: Optional[Any] = None,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generate plain-language explanations for top_n matched schemes.

    - Makes one Groq call for all top_n schemes.
    - Validates:
      * Drops returned IDs not in input.
      * Reverts documents_needed to original list if count mismatches.
      * Limits how_to_apply to max 5 steps.
    - Fallback:
      * Triggers on Groq error, timeout, invalid JSON, or missing scheme.
      * Marks each result source="llm" or "fallback".
    - Merges with structured fields: id, name, level, benefits, official_url, score.
    """
    if not matches:
        return []

    target_matches = matches[:top_n]
    valid_ids = {m.scheme.id for m in target_matches}
    input_docs_by_id = {m.scheme.id: m.scheme.documents_required[:8] for m in target_matches}

    llm_results_by_id: Dict[str, Dict[str, Any]] = {}
    llm_success = False

    # Attempt LLM call
    try:
        system_prompt = build_system_prompt(language=profile.language)
        user_prompt = build_user_prompt(target_matches, profile, top_n=top_n)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        raw_response = call_groq(messages=messages, client=client, model=model)
        parsed_json = json.loads(raw_response)

        if isinstance(parsed_json, dict) and "results" in parsed_json and isinstance(parsed_json["results"], list):
            for item in parsed_json["results"]:
                if isinstance(item, dict) and "id" in item:
                    item_id = str(item["id"]).strip()
                    # Drop returned ids not in input
                    if item_id in valid_ids:
                        llm_results_by_id[item_id] = item
            llm_success = True
    except Exception:
        # Fallback will handle all items
        llm_success = False

    # Merge explanations with structured fields
    results: List[Dict[str, Any]] = []
    for m in target_matches:
        scheme = m.scheme
        scheme_id = scheme.id

        if llm_success and scheme_id in llm_results_by_id:
            llm_item = llm_results_by_id[scheme_id]
            expected_docs = input_docs_by_id[scheme_id]
            returned_docs = llm_item.get("documents_needed")

            # Validate: documents_needed must have same count as input documents, else use original list
            if isinstance(returned_docs, list) and len(returned_docs) == len(expected_docs):
                documents_needed = returned_docs
            else:
                documents_needed = list(expected_docs)

            # Validate: how_to_apply max 5 steps
            returned_steps = llm_item.get("how_to_apply")
            if isinstance(returned_steps, list):
                how_to_apply = returned_steps[:5]
            else:
                how_to_apply = list(scheme.application_process[:5])

            summary = str(llm_item.get("summary", "")).strip()
            if not summary:
                fallback = build_fallback_explanation(m, profile)
                summary = fallback["summary"]

            why_you_qualify = str(llm_item.get("why_you_qualify", "")).strip()
            if not why_you_qualify:
                fallback = build_fallback_explanation(m, profile)
                why_you_qualify = fallback["why_you_qualify"]

            things_to_check = llm_item.get("things_to_check")
            if not isinstance(things_to_check, list):
                things_to_check = list(m.unverified_conditions)

            results.append({
                "id": scheme.id,
                "name": scheme.name,
                "level": scheme.level,
                "benefits": scheme.benefits,
                "official_url": scheme.official_url,
                "score": m.score,
                "summary": summary,
                "why_you_qualify": why_you_qualify,
                "things_to_check": things_to_check,
                "documents_needed": documents_needed,
                "how_to_apply": how_to_apply,
                "source": "llm",
            })
        else:
            # Fallback explanation
            results.append(build_fallback_explanation(m, profile))

    return results
