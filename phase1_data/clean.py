"""Main cleaning and transformation pipeline for Phase 1 Data Acquisition and Cleaning."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from phase1_data.schemas import Scheme, Eligibility, QualityReport
from phase1_data.parsers import (
    extract_states,
    extract_category_tags,
    extract_documents_required,
    extract_application_process,
    parse_eligibility_data,
)


def process_schemes_dataframe(df: pd.DataFrame) -> List[Scheme]:
    """Process raw DataFrame into validated Scheme models."""
    # Drop 'Unnamed: 9' if present
    if "Unnamed: 9" in df.columns:
        df = df.drop(columns=["Unnamed: 9"])

    # Drop duplicate slugs, keep first
    df = df.drop_duplicates(subset=["slug"], keep="first")

    # Replace NaNs with empty string
    df = df.fillna("")

    schemes: List[Scheme] = []
    for _, row in df.iterrows():
        slug = str(row.get("slug", "")).strip()
        if not slug:
            continue

        scheme_name = str(row.get("scheme_name", "")).strip()
        details = str(row.get("details", "")).strip()
        benefits = str(row.get("benefits", "")).strip()
        eligibility_text = str(row.get("eligibility", "")).strip()
        application = str(row.get("application", "")).strip()
        documents = str(row.get("documents", "")).strip()
        raw_level = str(row.get("level", "")).strip()
        level = raw_level.lower() if raw_level else "state"
        scheme_category = str(row.get("schemeCategory", "")).strip()
        tags = str(row.get("tags", "")).strip()

        # Extract states
        states = extract_states(level, scheme_name, details, eligibility_text)

        # Extract category tags
        category_tags = extract_category_tags(scheme_category, tags)

        # Extract documents and application process
        documents_required = extract_documents_required(documents)
        application_process = extract_application_process(application)

        # Extract structured eligibility
        eligibility_obj = parse_eligibility_data(eligibility_text, tags)

        # Build official URL
        official_url = f"https://www.myscheme.gov.in/schemes/{slug}"

        scheme = Scheme(
            id=slug,
            name=scheme_name,
            level=level,
            states=states,
            ministry=None,
            category_tags=category_tags,
            benefits=benefits if benefits else None,
            eligibility_text=eligibility_text if eligibility_text else None,
            eligibility=eligibility_obj,
            documents_required=documents_required,
            application_process=application_process,
            official_url=official_url,
            last_updated=None,
        )
        schemes.append(scheme)

    return schemes


def generate_quality_report(schemes: List[Scheme]) -> Dict[str, Any]:
    """Generate quality report with non-null % per eligibility field, count per state, and UNKNOWN count."""
    total = len(schemes)
    if total == 0:
        return {
            "total_schemes": 0,
            "eligibility_fields_non_null_pct": {},
            "state_counts": {},
            "unknown_count": 0,
        }

    # Count non-nulls / restrictions in eligibility
    min_age_count = sum(1 for s in schemes if s.eligibility.min_age is not None)
    max_age_count = sum(1 for s in schemes if s.eligibility.max_age is not None)
    income_count = sum(1 for s in schemes if s.eligibility.max_annual_income is not None)
    female_only_count = sum(1 for s in schemes if s.eligibility.genders == ["female"])
    category_specified_count = sum(1 for s in schemes if s.eligibility.social_categories != ["any"])
    occupation_specified_count = sum(1 for s in schemes if s.eligibility.occupations != ["any"])
    disability_count = sum(1 for s in schemes if s.eligibility.disability_required)
    bpl_count = sum(1 for s in schemes if s.eligibility.bpl_required)
    other_conditions_count = sum(1 for s in schemes if len(s.eligibility.other_conditions) > 0)

    # State counts
    state_counts: Dict[str, int] = {}
    unknown_count = 0
    for s in schemes:
        if s.states == ["UNKNOWN"]:
            unknown_count += 1
        for st in s.states:
            state_counts[st] = state_counts.get(st, 0) + 1

    report = {
        "total_schemes": total,
        "eligibility_fields_non_null_pct": {
            "min_age": round((min_age_count / total) * 100, 2),
            "max_age": round((max_age_count / total) * 100, 2),
            "max_annual_income": round((income_count / total) * 100, 2),
            "genders": 100.0,
            "social_categories": 100.0,
            "occupations": 100.0,
            "disability_required": round((disability_count / total) * 100, 2),
            "bpl_required": round((bpl_count / total) * 100, 2),
            "other_conditions": round((other_conditions_count / total) * 100, 2),
        },
        "state_counts": dict(sorted(state_counts.items(), key=lambda item: item[1], reverse=True)),
        "unknown_count": unknown_count,
        "summary": {
            "central_schemes": sum(1 for s in schemes if s.level == "central"),
            "state_schemes": sum(1 for s in schemes if s.level == "state"),
            "gender_restricted_count": female_only_count,
            "social_category_restricted_count": category_specified_count,
            "occupation_restricted_count": occupation_specified_count,
            "disability_required_count": disability_count,
            "bpl_required_count": bpl_count,
        }
    }
    return report


def run_pipeline(
    input_csv_path: str = "data/raw/updated_data.csv",
    output_json_path: str = "data/processed/schemes.json",
    report_json_path: str = "data/processed/quality_report.json"
) -> Dict[str, Any]:
    """Run Phase 1 data cleaning pipeline and save processed outputs."""
    print(f"Reading input CSV: {input_csv_path}")
    df = pd.read_csv(input_csv_path)

    print("Processing schemes and extracting eligibility...")
    schemes = process_schemes_dataframe(df)

    print(f"Processed {len(schemes)} valid schemes.")

    # Ensure output directory exists
    output_dir = Path(output_json_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save schemes.json
    print(f"Saving schemes to {output_json_path}")
    schemes_data = [scheme.model_dump() for scheme in schemes]
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(schemes_data, f, indent=2, ensure_ascii=False)

    # Generate and save quality report
    print(f"Generating quality report and saving to {report_json_path}")
    report = generate_quality_report(schemes)
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("Phase 1 pipeline completed successfully.")
    return report


if __name__ == "__main__":
    run_pipeline()
