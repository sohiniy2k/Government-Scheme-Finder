"""Loader for processed scheme dataset and categories derivation."""

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from phase1_data.schemas import Scheme
from phase1_data.constants import SCHEME_CATEGORIES


@lru_cache(maxsize=1)
def load_schemes(file_path: str = "data/processed/schemes.json") -> List[Scheme]:
    """
    Load data/processed/schemes.json once into memory.
    Cached via @lru_cache so it loads once, reusable across calls and Phase 4.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Schemes file not found at: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    return [Scheme.model_validate(item) for item in raw_data]


def get_categories(schemes: Optional[List[Scheme]] = None) -> List[str]:
    """
    Derive the category list from category_tags matching the 19 schemeCategory values.
    """
    if schemes is None:
        schemes = load_schemes()

    canonical_map = {c.lower(): c for c in SCHEME_CATEGORIES}
    derived = set()

    for s in schemes:
        for tag in s.category_tags:
            tag_clean = tag.strip().lower()
            if tag_clean in canonical_map:
                derived.add(canonical_map[tag_clean])

    return sorted(list(derived))
