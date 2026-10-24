"""User Profile schema for Phase 2 matching based on ARCHITECTURE.md 6.2."""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator
from phase1_data.constants import STATES_AND_UTS, OCCUPATIONS

# constants list minus "any", plus "other"
PROFILE_OCCUPATIONS = [occ for occ in OCCUPATIONS if occ != "any"] + ["other"]

GenderType = Literal["male", "female", "transgender", "prefer_not_to_say"]
SocialCategoryType = Literal["General", "SC", "ST", "OBC", "EWS", "Minority", "prefer_not_to_say"]
BplType = Literal["yes", "no", "unknown"]
LanguageType = Literal["en", "hi"]


class UserProfile(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Age in years (0-120)")
    state: str = Field(..., description="One of the 36 Indian states or Union Territories")
    annual_income: int = Field(..., ge=0, description="Annual family income in rupees (>= 0)")
    occupation: str = Field(..., description="Occupation from approved profile occupations list")
    gender: GenderType = Field(..., description="Gender (male/female/transgender/prefer_not_to_say)")
    social_category: SocialCategoryType = Field(..., description="Social category (General/SC/ST/OBC/EWS/Minority/prefer_not_to_say)")
    disability: bool = Field(default=False, description="Whether user has a certified disability (Divyangjan)")
    bpl: BplType = Field(default="unknown", description="Below Poverty Line status (yes/no/unknown)")
    interests: Optional[List[str]] = Field(default_factory=list, description="Optional list of categories/interests")
    language: LanguageType = Field(default="en", description="Output language preference (en/hi)")

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in STATES_AND_UTS:
            raise ValueError(f"Invalid state '{v}'. Must be one of the 36 States/UTs.")
        return v

    @field_validator("occupation")
    @classmethod
    def validate_occupation(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in PROFILE_OCCUPATIONS:
            raise ValueError(
                f"Invalid occupation '{v}'. Must be one of: {', '.join(PROFILE_OCCUPATIONS)}"
            )
        return v_clean
