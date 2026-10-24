"""Prompt generation for Groq LLM scheme explanations."""

import json
from typing import List, Dict, Any
from phase2_matching.profile import UserProfile
from phase2_matching.matcher import SchemeMatch


def build_system_prompt(language: str = "en") -> str:
    """
    Construct the system prompt enforcing strict grounding, language selection,
    and JSON schema.
    """
    lang_instruction = (
        "Respond in simple Hindi (हिंदी), but keep all official scheme names in their original official English/given form."
        if language == "hi"
        else "Respond in simple English, keeping all official scheme names as given."
    )

    return f"""You are an AI assistant helping Indian citizens understand government schemes.
Follow these strict rules:
1. Grounding: Use ONLY the provided scheme data. NEVER invent or hallucinate schemes, benefits, amounts, conditions, or documents.
2. Simplicity: Use simple, plain words suitable for a Class 8 student. Avoid complex administrative jargon.
3. Language: {lang_instruction}
4. Accuracy: Explain each scheme clearly: what benefit the citizen receives, why they qualify based on match reasons, conditions they must confirm, documents required, and application steps.
5. Format: Return ONLY valid JSON in this exact structure with no extra text or markdown formatting outside JSON:
{{
  "results": [
    {{
      "id": "scheme_slug_here",
      "summary": "1-2 simple sentences explaining the benefit.",
      "why_you_qualify": "Plain language explanation based on match reasons.",
      "things_to_check": ["Condition 1 to verify", "Condition 2 to verify"],
      "documents_needed": ["Document 1", "Document 2"],
      "how_to_apply": ["Step 1 description", "Step 2 description"]
    }}
  ]
}}"""


def prepare_prompt_payload(matches: List[SchemeMatch], profile: UserProfile, top_n: int = 5) -> Dict[str, Any]:
    """
    Build the structured payload containing only allowed scheme fields and
    profile information without personal identifiers.
    
    Allowed per-scheme fields:
    - id
    - name
    - level
    - benefits (max 500 chars)
    - match_reasons
    - unverified_conditions
    - documents_required (max 8)
    - application_process (max 5 steps)
    """
    schemes_payload = []
    for m in matches[:top_n]:
        scheme = m.scheme
        benefits_text = (scheme.benefits or "").strip()
        if len(benefits_text) > 500:
            benefits_text = benefits_text[:500]

        docs = scheme.documents_required[:8] if scheme.documents_required else []
        app_steps = scheme.application_process[:5] if scheme.application_process else []

        schemes_payload.append({
            "id": scheme.id,
            "name": scheme.name,
            "level": scheme.level,
            "benefits": benefits_text,
            "match_reasons": list(m.match_reasons),
            "unverified_conditions": list(m.unverified_conditions),
            "documents_required": docs,
            "application_process": app_steps,
        })

    # Non-identifiable profile context
    profile_payload = {
        "age": profile.age,
        "state": profile.state,
        "occupation": profile.occupation,
        "gender": profile.gender,
        "social_category": profile.social_category,
        "disability": profile.disability,
        "bpl": profile.bpl,
        "interests": profile.interests if profile.interests else [],
    }

    return {
        "citizen_profile": profile_payload,
        "schemes": schemes_payload,
        "language": profile.language,
    }


def build_user_prompt(matches: List[SchemeMatch], profile: UserProfile, top_n: int = 5) -> str:
    """Generate user prompt containing the JSON payload."""
    payload = prepare_prompt_payload(matches, profile, top_n=top_n)
    return (
        f"Explain the following matched schemes for this citizen profile in the requested language ({profile.language}):\n\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )
