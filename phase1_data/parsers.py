"""Extraction and parsing logic for eligibility, money, age, states, and text fields."""

import re
from typing import Optional, List, Tuple
from phase1_data.constants import (
    STATES_AND_UTS,
    STATE_PATTERNS,
    OCCUPATIONS,
)
from phase1_data.schemas import Eligibility

# Regex patterns for applicant mentions vs others
APPLICANT_KEYWORD_RE = re.compile(
    r'\b(applicant|candidate|student|beneficiary|applicants|candidates|students|beneficiaries)\b',
    re.IGNORECASE
)
OTHERS_KEYWORD_RE = re.compile(
    r'\b(deceased|child|children|bride)\b',
    re.IGNORECASE
)

# Occupation regex patterns
OCCUPATION_PATTERNS = {
    "student": re.compile(r'\b(student|students|studying|scholarship)\b', re.IGNORECASE),
    "farmer": re.compile(r'\b(farmer|farmers|agriculture|agricultural|cultivator|cultivators|kisan)\b', re.IGNORECASE),
    "fisherman": re.compile(r'\b(fisherman|fishermen|fisheries|fishery|fishers?)\b', re.IGNORECASE),
    "artisan": re.compile(r'\b(artisan|artisans|craftsmen|craftsman|weaver|weavers)\b', re.IGNORECASE),
    "construction_worker": re.compile(r'\b(construction\s+worker|construction\s+workers|construction\s+labour|building\s+and\s+other\s+construction)\b', re.IGNORECASE),
    "entrepreneur": re.compile(r'\b(entrepreneur|entrepreneurs|startup|startups|business\s+owner|self-employed)\b', re.IGNORECASE),
    "unemployed": re.compile(r'\b(unemployed|unemployment|job\s+seeker|jobseekers?)\b', re.IGNORECASE),
    "senior_citizen": re.compile(r'\b(senior\s+citizen|senior\s+citizens|elderly|pensioner|pensioners)\b', re.IGNORECASE),
}

# Compiled state patterns
COMPILED_STATE_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), canonical_name)
    for pattern, canonical_name in STATE_PATTERNS
]


def split_sentences(text: str) -> List[str]:
    """
    Split single-line text into sentences ending with '. '.
    Does not split on 'Rs.' followed by a space.
    """
    if not text:
        return []
    
    # Split on period followed by space(s), where period is not preceded by 'Rs' or 'INR'
    raw_sentences = re.split(r'(?<!\bRs)(?<!\bINR)\.\s+', text.strip(), flags=re.IGNORECASE)
    sentences = []
    for s in raw_sentences:
        s_clean = s.strip()
        if s_clean.endswith('.'):
            s_clean = s_clean[:-1].strip()
        if s_clean:
            sentences.append(s_clean)
    return sentences


def parse_money_amount(text: str) -> Optional[int]:
    """
    Parse a single money string or extract amounts from text.
    Handles:
    - '₹1,80,000/-'
    - '₹ 1,00,000'
    - 'Rs. 75000'
    - '2 lakh'
    - '₹8 lakh'
    - '1.5 lakh'
    Multiple amounts -> largest.
    """
    if not text:
        return None
    amounts = extract_all_money_amounts(text)
    return max(amounts) if amounts else None


def extract_all_money_amounts(text: str) -> List[int]:
    """Extract all money amounts from text in integer rupees."""
    amounts: List[int] = []

    # 1. Lakh patterns: optional currency + number + lakh/lac
    lakh_re = re.compile(r'(?:(?:₹|rs\.?|inr)\s*)?(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?)\b', re.IGNORECASE)
    for match in lakh_re.finditer(text):
        try:
            val = float(match.group(1)) * 100000
            amounts.append(int(round(val)))
        except ValueError:
            pass

    # 2. Currency symbol / Rs. with numbers (excluding amounts followed by lakh/lac)
    curr_re = re.compile(r'(?:₹|rs\.?|inr)\s*([0-9,]+)(?:\s*/-|\s*/\s*-)?(?!\s*(?:lakh|lac))', re.IGNORECASE)
    for match in curr_re.finditer(text):
        clean_num = match.group(1).replace(',', '').strip()
        if clean_num.isdigit():
            amounts.append(int(clean_num))

    # 3. Formatted numbers with commas (e.g. 1,80,000) without currency symbol
    comma_re = re.compile(r'\b([0-9]{1,3}(?:,[0-9]{2,3})+)(?:\s*/-)?(?!\s*(?:lakh|lac))\b', re.IGNORECASE)
    for match in comma_re.finditer(text):
        clean_num = match.group(1).replace(',', '').strip()
        if clean_num.isdigit():
            amounts.append(int(clean_num))

    return amounts


def parse_income_from_sentence(sentence: str) -> Optional[int]:
    """Extract income amount if sentence contains 'income'."""
    if not re.search(r'\bincome\b', sentence, re.IGNORECASE):
        return None
    amounts = extract_all_money_amounts(sentence)
    return max(amounts) if amounts else None


def parse_applicant_age(sentence: str) -> Tuple[Optional[int], Optional[int], bool]:
    """
    Extract (min_age, max_age, is_applicant_age) from a sentence.
    Only extracts if applicant/candidate/student/beneficiary is mentioned
    and not about others (deceased, child, bride).
    
    Supported patterns:
    - '18 to 60 years'
    - '18-60 years'
    - 'between X and Y'
    - 'under/below/less than X years'
    - 'above/at least/attained X years'
    """
    # Must mention applicant keyword
    if not APPLICANT_KEYWORD_RE.search(sentence):
        return None, None, False

    # Must NOT be about others (deceased, child, bride)
    if OTHERS_KEYWORD_RE.search(sentence):
        return None, None, False

    min_age: Optional[int] = None
    max_age: Optional[int] = None
    matched = False

    # 1. Range: between X and Y
    m_between = re.search(r'\bbetween\s+(\d{1,2})\s*(?:and|to)\s*(\d{1,2})\b', sentence, re.IGNORECASE)
    if m_between:
        min_age = int(m_between.group(1))
        max_age = int(m_between.group(2))
        return min_age, max_age, True

    # 2. Range: X to Y years (or X upto Y years)
    m_to = re.search(r'\b(\d{1,2})\s*(?:to|upto|up to)\s*(\d{1,2})\s*(?:years|yrs)?\b', sentence, re.IGNORECASE)
    if m_to:
        min_age = int(m_to.group(1))
        max_age = int(m_to.group(2))
        return min_age, max_age, True

    # 3. Range: X-Y years
    m_hyphen = re.search(r'\b(\d{1,2})\s*-\s*(\d{1,2})\s*(?:years|yrs)?\b', sentence, re.IGNORECASE)
    if m_hyphen:
        min_age = int(m_hyphen.group(1))
        max_age = int(m_hyphen.group(2))
        return min_age, max_age, True

    # 4. Upper bound: under / below / less than X years
    m_upper = re.search(r'\b(?:under|below|less than)(?:\s+(?:the\s+)?age(?:\s+of)?)?\s+(\d{1,2})\s*(?:years|yrs)?\b', sentence, re.IGNORECASE)
    if m_upper:
        max_age = int(m_upper.group(1))
        matched = True

    # 5. Lower bound: above / at least / attained X years
    m_lower = re.search(r'\b(?:above|at least|attained)(?:\s+(?:the\s+)?age(?:\s+of)?)?\s+(\d{1,2})\s*(?:years|yrs)?\b', sentence, re.IGNORECASE)
    if m_lower:
        min_age = int(m_lower.group(1))
        matched = True

    return min_age, max_age, matched


def parse_genders(eligibility_text: str) -> List[str]:
    """["female"] if applicant must be women/woman/girl/female/widow/mother, else ["any"]."""
    if not eligibility_text:
        return ["any"]
    if re.search(r'\b(women|woman|girl|girls|female|females|widow|widows|mother|mothers)\b', eligibility_text, re.IGNORECASE):
        return ["female"]
    return ["any"]


def parse_social_categories(eligibility_text: str) -> List[str]:
    """SC, ST, OBC, EWS, Minority via regex, else ["any"]."""
    if not eligibility_text:
        return ["any"]

    cats: List[str] = []
    if re.search(r'\bSC\b', eligibility_text) or re.search(r'\bscheduled\s+caste\b', eligibility_text, re.IGNORECASE):
        cats.append("SC")
    if re.search(r'\bST\b', eligibility_text) or re.search(r'\bscheduled\s+tribe\b', eligibility_text, re.IGNORECASE):
        cats.append("ST")
    if re.search(r'\bOBC\b', eligibility_text, re.IGNORECASE) or re.search(r'\bother\s+backward\b', eligibility_text, re.IGNORECASE):
        cats.append("OBC")
    if re.search(r'\bEWS\b', eligibility_text, re.IGNORECASE) or re.search(r'\beconomically\s+weaker\b', eligibility_text, re.IGNORECASE):
        cats.append("EWS")
    if re.search(r'minorit', eligibility_text, re.IGNORECASE):
        cats.append("Minority")

    return cats if cats else ["any"]


def parse_occupations(eligibility_text: str, tags: str = "") -> List[str]:
    """
    Match occupations from eligibility + tags keywords using OCCUPATIONS list.
    Returns matched occupations or ["any"].
    """
    combined = f"{eligibility_text or ''} {tags or ''}"
    matched = []
    for occ, pattern in OCCUPATION_PATTERNS.items():
        if pattern.search(combined):
            matched.append(occ)
    return matched if matched else ["any"]


def find_states_in_text(text: str) -> List[str]:
    """
    Find 36 states/UTs in text using word boundaries.
    Multi-word and aliases match into canonical names.
    """
    if not text:
        return []
    
    found = set()
    for compiled_re, canonical_name in COMPILED_STATE_PATTERNS:
        if compiled_re.search(text):
            found.add(canonical_name)
            
    return sorted(list(found))


def extract_states(level: str, scheme_name: str, details: str, eligibility: str) -> List[str]:
    """
    states: central -> ["ALL"].
    state -> word-boundary match of 36 states/UTs in scheme_name, else details, else eligibility.
    No match -> ["UNKNOWN"].
    """
    if str(level).strip().lower() == "central":
        return ["ALL"]

    # Try scheme_name
    s = find_states_in_text(scheme_name)
    if s:
        return s

    # Try details
    s = find_states_in_text(details)
    if s:
        return s

    # Try eligibility
    s = find_states_in_text(eligibility)
    if s:
        return s

    return ["UNKNOWN"]


def extract_category_tags(scheme_category: str, tags: str) -> List[str]:
    """category_tags = schemeCategory + tags, split, trimmed, deduped."""
    tokens: List[str] = []
    for text_val in [scheme_category, tags]:
        if text_val:
            parts = [p.strip() for p in str(text_val).split(",") if p.strip()]
            tokens.extend(parts)

    seen = set()
    result = []
    for t in tokens:
        t_lower = t.lower()
        if t_lower not in seen:
            seen.add(t_lower)
            result.append(t)
    return result


def extract_documents_required(documents_text: str) -> List[str]:
    """documents_required: split on '. '."""
    if not documents_text:
        return []
    docs = []
    for doc in str(documents_text).split(". "):
        clean_doc = doc.strip().rstrip(".").strip()
        if clean_doc:
            docs.append(clean_doc)
    return docs


def extract_application_process(application_text: str) -> List[str]:
    """application_process: split on 'Step \\d+:'."""
    if not application_text:
        return []
    text_str = str(application_text).strip()
    if not text_str:
        return []

    if re.search(r'Step\s*\d+\s*:', text_str, re.IGNORECASE):
        parts = re.split(r'Step\s*\d+\s*:\s*', text_str, flags=re.IGNORECASE)
        steps = [p.strip() for p in parts if p.strip()]
        return steps
    else:
        return [text_str]


def parse_eligibility_data(eligibility_text: str, tags: str = "") -> Eligibility:
    """
    Parse structured eligibility criteria from eligibility text according to requirements:
    - max_annual_income: sentence with 'income' + amount. Multiple amounts -> largest.
    - min_age/max_age: only from sentences mentioning applicant/candidate/student/beneficiary.
    - age sentences about others (deceased, child, bride) -> other_conditions.
    - genders: ['female'] if women/woman/girl/female/widow/mother, else ['any'].
    - social_categories: SC, ST, OBC, EWS, Minority via regex, else ['any'].
    - occupations from eligibility + tags keywords using OCCUPATIONS list.
    - disability_required: true if divyang/disab/PwD.
    - bpl_required: true if BPL/below poverty line.
    - other_conditions: unused eligibility sentences.
    """
    elig_str = str(eligibility_text or "").strip()
    sentences = split_sentences(elig_str)
    used_sentences = set()

    # 1. Income
    income_amounts: List[int] = []
    for sent in sentences:
        inc = parse_income_from_sentence(sent)
        if inc is not None:
            income_amounts.append(inc)
            used_sentences.add(sent)
    max_annual_income = max(income_amounts) if income_amounts else None

    # 2. Age
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    for sent in sentences:
        s_min, s_max, is_applicant = parse_applicant_age(sent)
        if is_applicant:
            if s_min is not None:
                min_age = s_min
            if s_max is not None:
                max_age = s_max
            used_sentences.add(sent)

    # 3. Genders
    genders = parse_genders(elig_str)

    # 4. Social Categories
    social_categories = parse_social_categories(elig_str)

    # 5. Occupations
    occupations = parse_occupations(elig_str, tags)

    # 6. Disability & BPL
    disability_required = bool(re.search(r'\b(divyang|divyangjan|disab\w*|pwd)\b', elig_str, re.IGNORECASE))
    bpl_required = bool(re.search(r'\b(bpl|below\s+poverty\s+line)\b', elig_str, re.IGNORECASE))

    # 7. Other conditions: unused eligibility sentences
    other_conditions = [s for s in sentences if s not in used_sentences]

    return Eligibility(
        min_age=min_age,
        max_age=max_age,
        genders=genders,
        social_categories=social_categories,
        max_annual_income=max_annual_income,
        occupations=occupations,
        disability_required=disability_required,
        bpl_required=bpl_required,
        other_conditions=other_conditions,
    )
