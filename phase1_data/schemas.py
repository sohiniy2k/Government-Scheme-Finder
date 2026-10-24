"""Pydantic schemas for Phase 1 Scheme Data according to ARCHITECTURE.md 6.1."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Eligibility(BaseModel):
    min_age: Optional[int] = Field(default=None, description="Minimum age limit in years or null")
    max_age: Optional[int] = Field(default=None, description="Maximum age limit in years or null")
    genders: List[str] = Field(default_factory=lambda: ["any"], description="Target genders e.g. ['female'] or ['any']")
    social_categories: List[str] = Field(default_factory=lambda: ["any"], description="Target categories e.g. ['SC', 'ST'] or ['any']")
    max_annual_income: Optional[int] = Field(default=None, description="Maximum annual family income in rupees or null")
    occupations: List[str] = Field(default_factory=lambda: ["any"], description="Target occupations or ['any']")
    disability_required: bool = Field(default=False, description="True if scheme requires disability/Divyang/PwD")
    bpl_required: bool = Field(default=False, description="True if scheme requires BPL/below poverty line")
    other_conditions: List[str] = Field(default_factory=list, description="Unused eligibility sentences")


class Scheme(BaseModel):
    id: str = Field(..., description="Unique scheme slug")
    name: str = Field(..., description="Official scheme name")
    level: str = Field(..., description="'central' or 'state'")
    states: List[str] = Field(..., description="Target states/UTs e.g. ['ALL'], ['Maharashtra'], or ['UNKNOWN']")
    ministry: Optional[str] = Field(default=None, description="Ministry name or null")
    category_tags: List[str] = Field(default_factory=list, description="Merged, trimmed, deduplicated categories and tags")
    benefits: Optional[str] = Field(default=None, description="Raw benefits description")
    eligibility_text: Optional[str] = Field(default=None, description="Original eligibility text from source")
    eligibility: Eligibility = Field(..., description="Structured eligibility criteria")
    documents_required: List[str] = Field(default_factory=list, description="Required documents split by sentence")
    application_process: List[str] = Field(default_factory=list, description="Steps for application split by 'Step \\d+:'")
    official_url: Optional[str] = Field(default=None, description="Official portal URL")
    last_updated: Optional[str] = Field(default=None, description="Date of last update or null")


class QualityReport(BaseModel):
    total_schemes: int
    eligibility_fields_non_null_pct: Dict[str, float]
    state_counts: Dict[str, int]
    unknown_count: int
    summary: Optional[Dict[str, Any]] = None
