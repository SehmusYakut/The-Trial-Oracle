"""Pydantic models for clinical trial data."""
from pydantic import BaseModel, Field
from typing import List, Optional


class EligibilityCriteria(BaseModel):
    inclusion: List[str] = Field(default_factory=list)
    exclusion: List[str] = Field(default_factory=list)


class TrialData(BaseModel):
    nct_id: str
    title: str
    conditions: List[str] = Field(default_factory=list)
    eligibility: EligibilityCriteria
    status: Optional[str] = None
    phase: Optional[str] = None


class TrialRequest(BaseModel):
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT identifier, e.g. NCT04280705")
