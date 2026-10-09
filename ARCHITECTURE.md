# Government Scheme Finder – Architecture

An AI-powered service that takes a citizen's profile (age, state, income, occupation, gender, category), matches it against real Indian government scheme data, uses an LLM (Groq) to explain each matching scheme in plain language (English or Hindi), and displays clear, actionable results including the documents needed and how to apply.

> Status: architecture only. No implementation yet.

---

## 1. Goals and Non-Goals

**Goals**

- Help people discover welfare schemes, scholarships, and subsidies they are likely eligible for.
- Explain each scheme simply: what you get, why you qualify, documents needed, how to apply.
- Support English and Hindi output (extensible to other languages).
- Be transparent: every recommendation shows *why* it matched.

**Non-Goals**

- This is not an official government service and does not submit applications.
- It does not guarantee eligibility; final eligibility is decided by the issuing department.
- It does not store any user's personal data.

---

## 2. Core Design Principle

**Eligibility is decided by deterministic code, not by the LLM.**

| Responsibility | Handled by | Why |
|---|---|---|
| Filtering schemes by age, state, income, gender, category, occupation | Rule-based matching engine (Python) | Predictable, testable, explainable, no hallucination |
| Ranking matched schemes | Scoring function (Python) | Consistent and tunable |
| Explaining schemes in plain language, translating, summarizing documents/steps | Groq LLM | This is what LLMs are good at |

The LLM only receives schemes that have already passed matching, and it is instructed to use only the provided data. This prevents it from inventing schemes or wrongly declaring someone eligible.

---

## 3. High-Level Architecture

```
┌──────────────────────┐
│  React UI (Phase 5)  │  profile form, dropdowns, language toggle, result cards
└──────────┬───────────┘
           │ HTTP (JSON)
┌──────────▼───────────┐
│  FastAPI (Phase 4)   │  /api/recommend, /api/meta, /api/schemes/{id}, /health
└──────────┬───────────┘
           │
   ┌───────┴─────────────────────┐
   │                             │
┌──▼──────────────────┐   ┌──────▼──────────────┐
│ Matching Engine     │   │ LLM Service         │
│ (Phase 2)           │──►│ (Phase 3, Groq)     │
│ validate profile,   │   │ plain-language      │
│ filter, score, rank │   │ explanation, Hindi  │
└──┬──────────────────┘   └─────────────────────┘
   │
┌──▼──────────────────────────┐
│ Clean Scheme Store (Phase 1)│  data/processed/schemes.json (or SQLite)
└──▲──────────────────────────┘
   │ one-time / periodic ETL
┌──┴──────────────────────────┐
│ Raw Data                    │  myScheme-based dataset (Kaggle / Hugging Face)
└─────────────────────────────┘    or data.gov.in, plus curated seed file
```

---

## 4. Tech Stack

| Layer | Choice |
|---|---|
| Data processing | Python, pandas |
| Storage | JSON file for MVP; SQLite if filtering grows complex |
| Backend | Python, FastAPI, Pydantic |
| LLM | Groq API (model configurable via env, e.g. a Llama 3.x 70B model) |
| Frontend | React (Vite) |
| Testing | pytest (backend), Vitest / React Testing Library (frontend) |
| Config | `.env` (`GROQ_API_KEY`, `GROQ_MODEL`) – never committed |
| Deployment (later) | Streamlit Community Cloud or Vercel |

---

## 5. Project Structure

```
gov-scheme-finder/
├── ARCHITECTURE.md
├── .env.example              # GROQ_API_KEY=, GROQ_MODEL=
├── .gitignore                # includes .env, data/raw/
├── phase1_data/              # download, clean, structure scheme data
│   ├── download.py
│   ├── clean.py
│   ├── extract_eligibility.py
│   └── tests/
├── phase2_matching/          # user profile model + matching engine
│   ├── profile.py
│   ├── matcher.py
│   ├── scorer.py
│   └── tests/
├── phase3_llm/               # Groq integration
│   ├── groq_client.py
│   ├── prompts.py
│   ├── explainer.py
│   └── tests/
├── phase4_api/               # FastAPI service
│   ├── main.py
│   ├── routes.py
│   ├── schemas.py
│   └── tests/
├── phase5_ui/                # React frontend
│   ├── src/
│   └── tests/
└── data/
    ├── raw/                  # downloaded files (git-ignored)
    └── processed/
        └── schemes.json      # clean, structured, deduplicated
```

---

## 6. Data Model

### 6.1 Scheme (after Phase 1 processing)

```json
{
  "id": "pm-kisan",
  "name": "Pradhan Mantri Kisan Samman Nidhi",
  "level": "central",                 // "central" | "state"
  "states": ["ALL"],                  // or ["Maharashtra", ...]
  "ministry": "Ministry of Agriculture & Farmers Welfare",
  "category_tags": ["agriculture", "income support"],
  "benefits": "Rs 6000 per year in three instalments",
  "eligibility_text": "Original eligibility text from source",
  "eligibility": {
    "min_age": 18,                    // null = no limit / unknown
    "max_age": null,
    "genders": ["any"],               // "male" | "female" | "transgender" | "any"
    "social_categories": ["any"],     // "SC" | "ST" | "OBC" | "EWS" | "General" | "Minority" | "any"
    "max_annual_income": null,        // integer rupees, e.g. 250000
    "occupations": ["farmer"],        // or ["any"]
    "other_conditions": ["Must own cultivable land"]
  },
  "documents_required": ["Aadhaar card", "Land records", "Bank account details"],
  "application_process": "Apply online via the official portal or CSC",
  "official_url": "https://...",
  "last_updated": "2026-01-15"
}
```

### 6.2 User Profile (Phase 2 input)

| Field | Type | Notes |
|---|---|---|
| age | int (0–120) | required |
| state | enum (36 states/UTs) | dropdown |
| annual_income | int (rupees) | UI may offer income bands |
| occupation | enum | student, farmer, salaried, self-employed, unemployed, daily-wage worker, homemaker, senior citizen/retired, other |
| gender | enum | male, female, transgender, prefer not to say |
| social_category | enum | General, OBC, SC, ST, EWS, Minority, prefer not to say |
| disability | bool (optional) | many schemes depend on it |
| language | enum | en, hi |

---

## 7. Phases

### Phase 1 – Data Acquisition and Cleaning

**Purpose:** Turn raw scheme data into a clean, structured, deduplicated dataset the matcher can rely on.

**Steps**

1. **Download** the dataset locally (do not stream on every request).
   - Primary: a myScheme-derived dataset from Kaggle or Hugging Face (verify availability and license before use).
   - Fallback: a hand-curated `seed_schemes.json` of 50–100 major central and state schemes, built from official portals.
2. **Clean**
   - Normalize text (whitespace, encoding, HTML remnants).
   - Normalize state names to a fixed list of 36 states/UTs.
   - Normalize money: `"₹2.5 lakh"`, `"2,50,000"` → `250000`.
   - Normalize age ranges: `"between 18 and 40 years"` → `min_age=18, max_age=40`.
   - Split documents and benefits into clean lists.
3. **Extract structured eligibility** from free text.
   - Rule-based regex for common patterns (age, income, gender, SC/ST/OBC).
   - Optional one-time LLM-assisted extraction for hard cases, saved to disk and spot-checked by a human. This runs offline, never at request time.
   - Unknown values stay `null` (meaning "not restricted / not specified"), never guessed.
4. **Deduplicate** by normalized name + level + state.
5. **Save** to `data/processed/schemes.json` and log a data-quality report (counts, % of fields missing).

**Tests**

- Money, age and state normalizers on known inputs.
- No duplicate IDs; every scheme has `id`, `name`, `level`, `states`.
- Schema validation of every record with Pydantic.

**Done when:** processed file loads cleanly, passes schema validation, and the quality report is generated.

---

### Phase 2 – User Input and Matching Engine

**Purpose:** Validate the user profile and deterministically find eligible schemes.

**Matching rules (hard filters)**

| Field | Rule |
|---|---|
| State | Scheme is `central`, or user's state is in `states` |
| Age | `min_age <= age <= max_age` (null bound = no limit) |
| Gender | Scheme gender is `any` or matches user |
| Category | Scheme category is `any` or includes user's category |
| Income | `max_annual_income` is null or `income <= max_annual_income` |
| Occupation | Scheme occupation is `any` or includes user's occupation |

If the user chooses "prefer not to say", that field is treated as *unknown*: schemes restricted on it are kept but marked "may be eligible – check condition".

**Scoring and ranking**

- Higher score for schemes that specifically target the user (e.g. a scheme for female students over a scheme for "any").
- Bonus for state-specific schemes (often less known, more valuable).
- Each result carries `match_reasons` (e.g. "Age 21 is within 18–25") and `unverified_conditions` (e.g. "Must own cultivable land").

**No-results handling:** if zero matches, report which single filter, if relaxed, would produce results (e.g. "3 schemes match if income is up to ₹3 lakh").

**Tests**

- Profile validation (invalid age, unknown state rejected).
- Each filter rule tested in isolation with fixture schemes.
- Central schemes appear for every state; state schemes only for their state.
- Ranking order and match reasons are correct.

**Done when:** given a profile, the engine returns a ranked, explained list of candidate schemes with no LLM involved.

---

### Phase 3 – LLM Integration (Groq)

**Purpose:** Use the **Groq LLM** to turn matched scheme data into clear, friendly, plain-language explanations.

**Inputs to the LLM:** the user profile (no name or identifying info) and the top N (e.g. 5–8) matched schemes with their structured data and match reasons.

**Output (strict JSON)** per scheme:

```json
{
  "id": "pm-kisan",
  "summary": "One or two simple sentences about what this scheme gives you.",
  "why_you_qualify": "Plain-language version of match_reasons.",
  "things_to_check": ["Conditions the user must confirm"],
  "documents_needed": ["..."],
  "how_to_apply": ["Step 1 ...", "Step 2 ..."]
}
```

**Prompt rules**

- Use only the scheme data provided. Do not add schemes or invent benefits, amounts, or documents.
- Use simple words (target reading level: a Class 8 student).
- Respond in the requested language (English or Hindi), keeping scheme names in their official form.
- Return only valid JSON.

**Components**

- `groq_client.py` – API wrapper, reads `GROQ_API_KEY` and `GROQ_MODEL` from `.env`, timeout and retry.
- `prompts.py` – system and user prompt templates.
- `explainer.py` – builds the prompt, calls Groq, parses and validates JSON, and cross-checks that every returned `id` exists in the input.

**Fallback:** if Groq fails or returns invalid JSON, return the structured Phase 2 data with a template-based explanation, so the user always gets results.

**Tests**

- Unit tests with a mocked Groq client (prompt building, JSON parsing, fallback path, hallucinated ID rejected).
- Integration test against the real Groq API once the key is in `.env` (English and Hindi).

---

### Phase 4 – Recommendation API

**Purpose:** Expose the pipeline (Phase 1 data → Phase 2 matching → Phase 3 explanation) through a FastAPI service.

**Endpoints**

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service and data status |
| GET | `/api/meta` | Dropdown values: states, occupations, categories, genders, languages |
| POST | `/api/recommend` | Profile in, ranked and explained schemes out |
| GET | `/api/schemes/{id}` | Full details of one scheme |

**`POST /api/recommend` response (shape)**

```json
{
  "count": 5,
  "language": "hi",
  "results": [
    {
      "id": "...",
      "name": "...",
      "level": "central",
      "benefits": "...",
      "summary": "...",
      "why_you_qualify": "...",
      "things_to_check": ["..."],
      "documents_needed": ["..."],
      "how_to_apply": ["..."],
      "official_url": "..."
    }
  ],
  "relaxation_hint": null,
  "disclaimer": "This is guidance only. Confirm eligibility on the official portal."
}
```

**Cross-cutting concerns**

- Data loaded once at startup and held in memory.
- In-memory cache keyed by (profile, language) to reduce Groq calls.
- CORS enabled for the UI origin.
- Final deduplication of results by scheme ID.
- No logging of user profiles.

**Tests:** FastAPI TestClient tests for all endpoints, validation errors (422), empty-result path, and LLM-fallback path.

---

### Phase 5 – User Interface (React)

**Purpose:** A clean, accessible, mobile-friendly page where anyone can find schemes in under a minute.

**Screens and components**

- **Profile form:** age input; dropdowns for state (all 36 states/UTs from `/api/meta`), occupation, gender, category; income input or income bands; optional disability checkbox; language toggle (English / हिन्दी).
- **Results list:** a card per scheme with name, central/state badge, benefit highlight, "Why you qualify", "Things to check", documents checklist, "How to apply" steps, and an official-site link.
- **States:** loading skeleton, friendly empty state showing the relaxation hint, and error state with retry.
- **Trust elements:** visible disclaimer, "no data stored" note, links only to official `.gov.in` sources.

**Design notes**

- Large touch targets and readable font sizes (many users will be on phones).
- Simple language in labels; tooltips explaining terms like "EWS".
- Print / share-friendly results so users can take the documents list to a CSC or office.

**Tests:** form validation, dropdowns populated from `/api/meta`, results rendering with mocked API, empty and error states.

---

## 8. End-to-End Request Flow

1. User fills the form and clicks **Find Schemes**.
2. UI sends `POST /api/recommend`.
3. API validates the profile (Phase 2 model).
4. Matching engine filters and ranks schemes from the in-memory store (Phase 1 data).
5. Top N candidates are sent to Groq for explanation in the chosen language (Phase 3).
6. API validates the LLM output, merges it with structured data, deduplicates, and responds.
7. UI renders scheme cards with documents and application steps.

---

## 9. Security, Privacy and Responsible AI

- `GROQ_API_KEY` only in `.env` locally and in platform secrets when deployed; `.env` is git-ignored.
- No names, phone numbers, Aadhaar numbers, or addresses are ever collected.
- Profiles are not persisted or logged.
- The LLM never decides eligibility and cannot introduce schemes not in the dataset.
- Every result includes the official link and a disclaimer.
- Each scheme shows `last_updated` so users know how fresh the data is.

---

## 10. Future Enhancements

- More languages (Tamil, Bengali, Marathi, Telugu, etc.).
- Natural-language input ("I am a 20-year-old SC girl studying in Bihar").
- Voice input and audio output for users with low literacy.
- Scheduled data refresh and change detection.
- Deadline reminders for scholarships.
- Deployment on Streamlit Community Cloud or Vercel.
