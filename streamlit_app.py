import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
import streamlit as st

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 1. At startup, copy GROQ_API_KEY and GROQ_MODEL from st.secrets into os.environ if present
load_dotenv()

if hasattr(st, "secrets"):
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"]).strip()
        if "GROQ_MODEL" in st.secrets and st.secrets["GROQ_MODEL"]:
            os.environ["GROQ_MODEL"] = str(st.secrets["GROQ_MODEL"]).strip()
    except Exception:
        pass

# 2. Reuse phase1_data constants, phase2_matching, and phase3_llm
from phase1_data.constants import STATES_AND_UTS
from phase2_matching.profile import UserProfile, PROFILE_OCCUPATIONS
from phase2_matching.loader import load_schemes as base_load_schemes, get_categories as base_get_categories
from phase2_matching.matcher import match as base_match
from phase3_llm.explainer import explain as base_explain

# 3. Label dictionary for English and Hindi
LABELS = {
    "en": {
        "title": "Government Scheme Finder",
        "subtitle": "Discover Indian welfare schemes and subsidies personalized for you",
        "profile_header": "Citizen Profile",
        "age": "Age (Years)",
        "state": "State / Union Territory",
        "income": "Annual Family Income (₹)",
        "occupation": "Occupation",
        "gender": "Gender",
        "social_category": "Social Category",
        "bpl": "BPL Status",
        "disability": "Person with Certified Disability (Divyangjan)",
        "interests": "Areas of Interest",
        "submit": "Find Schemes",
        "spinner": "Finding matching schemes and generating explanations...",
        "schemes_found": "Schemes Found",
        "central_vs_state": "Central vs State",
        "top_category": "Top Category",
        "why_you_qualify": "Why You Qualify",
        "things_to_check": "Conditions to Confirm",
        "documents_needed": "Required Documents Checklist",
        "how_to_apply": "How to Apply",
        "official_site": "Official Scheme Portal",
        "ai_badge": "AI Explained",
        "fallback_badge": "Basic Info",
        "more_schemes": "More Matching Schemes",
        "no_matches_title": "No Direct Matches Found",
        "no_matches_msg": "We couldn't find schemes matching all your exact criteria.",
        "relaxation_hint_prefix": "Suggested adjustment:",
        "initial_title": "Find Your Eligible Schemes",
        "initial_msg": "Fill in your profile details on the left sidebar and click 'Find Schemes' to discover personalized welfare programs.",
        "disclaimer": "This service helps you discover government schemes you may be eligible for, but does not guarantee eligibility or submit applications. Final eligibility is determined by the relevant government department.",
        "privacy": "🔒 We do not store or track any of your personal data.",
    },
    "hi": {
        "title": "सरकारी योजना खोजक",
        "subtitle": "अपने लिए व्यक्तिगत सरकारी कल्याणकारी योजनाएं और सब्सिडी खोजें",
        "profile_header": "नागरिक विवरण",
        "age": "आयु (वर्ष)",
        "state": "राज्य / केंद्र शासित प्रदेश",
        "income": "वार्षिक पारिवारिक आय (₹)",
        "occupation": "व्यवसाय",
        "gender": "लिंग",
        "social_category": "सामाजिक श्रेणी",
        "bpl": "बीपीएल स्थिति",
        "disability": "दिव्यांग व्यक्ति (दिव्यांगजन)",
        "interests": "रुचि के क्षेत्र",
        "submit": "पात्र योजनाएं खोजें",
        "spinner": "योजनाएं खोजी जा रही हैं और विवरण तैयार किया जा रहा है...",
        "schemes_found": "कुल योजनाएं",
        "central_vs_state": "केंद्रीय बनाम राज्य",
        "top_category": "प्रमुख श्रेणी",
        "why_you_qualify": "आप पात्र क्यों हैं",
        "things_to_check": "जांचने योग्य शर्तें",
        "documents_needed": "आवश्यक दस्तावेज़ चेकलिस्ट",
        "how_to_apply": "आवेदन कैसे करें",
        "official_site": "आधिकारिक पोर्टल",
        "ai_badge": "AI द्वारा स्पष्ट",
        "fallback_badge": "सामान्य जानकारी",
        "more_schemes": "अन्य संबंधित योजनाएं",
        "no_matches_title": "कोई प्रत्यक्ष योजना नहीं मिली",
        "no_matches_msg": "आपकी सभी सटीक शर्तों से मेल खाने वाली योजनाएं नहीं मिल सकीं।",
        "relaxation_hint_prefix": "सुझाया गया बदलाव:",
        "initial_title": "अपनी पात्र योजनाएं खोजें",
        "initial_msg": "बाएं साइडबार में अपना विवरण भरें और अपने लिए सरकारी योजनाएं खोजने के लिए 'पात्र योजनाएं खोजें' पर क्लिक करें।",
        "disclaimer": "यह सेवा आपको सरकारी योजनाओं को खोजने में मदद करती है, लेकिन अंतिम पात्रता संबंधित सरकारी विभाग द्वारा निर्धारित की जाती है।",
        "privacy": "🔒 हम आपका कोई भी व्यक्तिगत डेटा संग्रहीत या ट्रैक नहीं करते हैं।",
    },
}

# 4. Streamlit page configuration
st.set_page_config(
    page_title="Government Scheme Finder",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 5. Injected CSS for glassmorphism and custom styling
CUSTOM_CSS = """
<style>
/* Main app gradient background */
.stApp {
    background: linear-gradient(135deg, #5B1A86 0%, #C2187A 50%, #F06BA8 100%) !important;
    background-attachment: fixed !important;
    color: #FFFFFF !important;
    font-size: 16px !important;
}

/* Glassmorphism scheme cards */
.scheme-glass-card {
    background: rgba(40, 10, 60, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    color: #FFFFFF;
}

.scheme-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}

.scheme-card-title {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0;
}

.badge-pill {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    border: 1px solid #FF2DAA;
    background: rgba(255, 45, 170, 0.2);
    color: #FF66C4;
    display: inline-block;
}

.badge-source {
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    background: rgba(255, 255, 255, 0.15);
    color: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.2);
    display: inline-block;
}

.benefit-highlight-box {
    background: rgba(245, 217, 10, 0.15);
    border-left: 4px solid #F5D90A;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 12px 0;
    font-size: 15px;
    color: #FFFFFF;
}

.section-label {
    font-size: 13px;
    font-weight: 700;
    color: #F5D90A;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 12px;
    margin-bottom: 4px;
}

.checklist-item {
    padding: 4px 0;
    font-size: 15px;
    color: rgba(255, 255, 255, 0.9);
}

/* Stat Tiles */
div[data-testid="stMetric"] {
    background: rgba(40, 10, 60, 0.55) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 20px !important;
    padding: 16px 20px !important;
}

/* Yellow primary buttons with #2A0A3A text */
.stButton > button {
    background-color: #F5D90A !important;
    color: #2A0A3A !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 12px 24px !important;
    font-size: 16px !important;
    min-height: 44px !important;
    box-shadow: 0 4px 14px 0 rgba(245, 217, 10, 0.4) !important;
}

.stButton > button:hover {
    background-color: #FFE84D !important;
    color: #2A0A3A !important;
}

/* Link Button */
div[data-testid="stLinkButton"] > a {
    background-color: rgba(255, 255, 255, 0.15) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
}

div[data-testid="stLinkButton"] > a:hover {
    background-color: #FF2DAA !important;
    border-color: #FF2DAA !important;
    color: #FFFFFF !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# 6. Cached data loading
@st.cache_data
def get_cached_schemes():
    return base_load_schemes()


@st.cache_data
def get_cached_categories():
    schemes = get_cached_schemes()
    return base_get_categories(schemes)


# 7. Cached recommendation and explanation function per profile + language (1 hour expiry)
@st.cache_data(ttl=3600)
def get_cached_recommendations(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    profile = UserProfile(**profile_dict)
    schemes = get_cached_schemes()
    matches = base_match(profile, schemes=schemes, top_n=10)

    if not matches:
        return {
            "results": [],
            "more_schemes": [],
            "relaxation_hint": matches.relaxation_hint,
        }

    # Top 5 explained via Phase 3
    top_matches = matches[:5]
    explained_results = base_explain(top_matches, profile, top_n=5)

    # Next 5 as more_schemes (compact preview)
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
    for r in explained_results:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            deduped_results.append(r)

    deduped_more = []
    for s in more_schemes:
        if s["id"] not in seen_ids:
            seen_ids.add(s["id"])
            deduped_more.append(s)

    return {
        "results": deduped_results,
        "more_schemes": deduped_more,
        "relaxation_hint": matches.relaxation_hint,
    }


# 8. Load baseline data
all_schemes = get_cached_schemes()
available_categories = get_cached_categories()

# 9. Sidebar: Form Inputs & Language Selection
with st.sidebar:
    # Language toggle
    lang_choice = st.radio(
        "Language / भाषा",
        options=["en", "hi"],
        format_func=lambda x: "English" if x == "en" else "हिंदी",
        horizontal=True,
    )
    txt = LABELS[lang_choice]

    st.markdown(f"### 📋 {txt['profile_header']}")

    # Form inputs
    age = st.number_input(
        txt["age"],
        min_value=0,
        max_value=120,
        value=25,
        step=1,
    )

    state = st.selectbox(
        txt["state"],
        options=STATES_AND_UTS,
        index=STATES_AND_UTS.index("Maharashtra") if "Maharashtra" in STATES_AND_UTS else 0,
    )

    annual_income = st.number_input(
        txt["income"],
        min_value=0,
        value=150000,
        step=10000,
    )

    occupation = st.selectbox(
        txt["occupation"],
        options=PROFILE_OCCUPATIONS,
        format_func=lambda o: o.replace("_", " ").title(),
        index=0,
    )

    gender = st.selectbox(
        txt["gender"],
        options=["male", "female", "transgender", "prefer_not_to_say"],
        format_func=lambda g: g.replace("_", " ").title(),
    )

    social_category = st.selectbox(
        txt["social_category"],
        options=["General", "SC", "ST", "OBC", "EWS", "Minority", "prefer_not_to_say"],
    )

    bpl = st.selectbox(
        txt["bpl"],
        options=["yes", "no", "unknown"],
        format_func=lambda b: b.upper(),
        index=2,
    )

    disability = st.checkbox(
        txt["disability"],
        value=False,
    )

    interests = st.multiselect(
        txt["interests"],
        options=available_categories,
        default=[],
    )

    submit_clicked = st.button(f"🔍 {txt['submit']}", use_container_width=True)

# 10. Main Header
txt = LABELS[lang_choice]
st.title(f"🇮🇳 {txt['title']}")
st.markdown(f"*{txt['subtitle']}*")
st.markdown("---")

# Session state initialization
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "has_searched" not in st.session_state:
    st.session_state.has_searched = False

# Process submission
if submit_clicked:
    profile_payload = {
        "age": int(age),
        "state": state,
        "annual_income": int(annual_income),
        "occupation": occupation,
        "gender": gender,
        "social_category": social_category,
        "disability": disability,
        "bpl": bpl,
        "interests": interests,
        "language": lang_choice,
    }

    with st.spinner(txt["spinner"]):
        st.session_state.recommendations = get_cached_recommendations(profile_payload)
        st.session_state.has_searched = True

# 11. Results Display
recs = st.session_state.recommendations

if recs is not None and st.session_state.has_searched:
    results = recs.get("results", [])
    more_schemes = recs.get("more_schemes", [])
    relaxation_hint = recs.get("relaxation_hint")

    total_count = len(results) + len(more_schemes)

    if total_count > 0:
        # Stat Tiles
        central_count = sum(1 for s in (results + more_schemes) if str(s.get("level", "")).lower() == "central")
        state_count = total_count - central_count

        # Top category calculation
        category_counts: Dict[str, int] = {}
        for s in results:
            for cat in s.get("category_tags", []):
                category_counts[cat] = category_counts.get(cat, 0) + 1

        top_category = max(category_counts, key=category_counts.get) if category_counts else (interests[0] if interests else "Welfare")

        col1, col2, col3 = st.columns(3)
        col1.metric(txt["schemes_found"], f"{total_count}")
        col2.metric(txt["central_vs_state"], f"{central_count} C · {state_count} S")
        col3.metric(txt["top_category"], str(top_category))

        st.markdown("<br>", unsafe_allow_html=True)

        # Explained Scheme Cards
        for scheme in results:
            is_central = str(scheme.get("level", "")).lower() == "central"
            level_label = "Central" if is_central else "State"
            source_badge = txt["ai_badge"] if scheme.get("source") == "llm" else txt["fallback_badge"]

            with st.container():
                st.markdown(
                    f"""
                    <div class="scheme-glass-card">
                        <div class="scheme-card-header">
                            <div>
                                <h2 class="scheme-card-title">{scheme.get("name", "")}</h2>
                                <p style="color: rgba(255,255,255,0.8); margin-top: 6px;">{scheme.get("summary", "")}</p>
                            </div>
                            <div>
                                <span class="badge-pill">{level_label}</span>
                                <span class="badge-source">{source_badge}</span>
                            </div>
                        </div>
                        <div class="benefit-highlight-box">
                            <strong>💰 Benefit:</strong> {scheme.get("benefits", "Direct welfare assistance")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Why you qualify
                if scheme.get("why_you_qualify"):
                    st.markdown(f"**🌟 {txt['why_you_qualify']}**")
                    st.write(scheme["why_you_qualify"])

                # Things to check
                if scheme.get("things_to_check"):
                    st.markdown(f"**⚠️ {txt['things_to_check']}**")
                    for cond in scheme["things_to_check"]:
                        st.markdown(f"- {cond}")

                # Documents checklist
                if scheme.get("documents_needed"):
                    st.markdown(f"**📑 {txt['documents_needed']}**")
                    for doc in scheme["documents_needed"]:
                        st.markdown(f"✓ &nbsp; {doc}")

                # How to apply
                if scheme.get("how_to_apply"):
                    st.markdown(f"**🚀 {txt['how_to_apply']}**")
                    for idx, step in enumerate(scheme["how_to_apply"], start=1):
                        st.markdown(f"**{idx}.** {step}")

                # Link to official portal
                if scheme.get("official_url"):
                    st.link_button(f"🏛️ {txt['official_site']} ↗", scheme["official_url"])

                st.markdown("---")

        # More Schemes Expander
        if more_schemes:
            with st.expander(f"📁 {txt['more_schemes']} ({len(more_schemes)})"):
                for more in more_schemes:
                    st.markdown(f"### {more.get('name')}")
                    st.caption(f"Level: {more.get('level', '').upper()}")
                    if more.get("benefits"):
                        st.write(more["benefits"])
                    if more.get("official_url"):
                        st.link_button(f"🏛️ {txt['official_site']} ↗", more["official_url"])
                    st.markdown("---")

    else:
        # Empty state when 0 schemes match
        st.markdown(
            f"""
            <div class="scheme-glass-card" style="text-align: center; padding: 40px;">
                <span style="font-size: 48px;">🔍</span>
                <h2>{txt['no_matches_title']}</h2>
                <p style="color: rgba(255,255,255,0.7);">{txt['no_matches_msg']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if relaxation_hint:
            st.info(f"💡 **{txt['relaxation_hint_prefix']}** {relaxation_hint}")

else:
    # Initial Welcome Screen
    st.markdown(
        f"""
        <div class="scheme-glass-card" style="text-align: center; padding: 40px;">
            <span style="font-size: 54px;">🏛️</span>
            <h2>{txt['initial_title']}</h2>
            <p style="color: rgba(255,255,255,0.8); max-width: 600px; margin: 0 auto;">
                {txt['initial_msg']}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 12. Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption(f"{txt['disclaimer']}")
st.markdown(f"<p style='color: #F5D90A; font-weight: 600;'>{txt['privacy']}</p>", unsafe_allow_html=True)
