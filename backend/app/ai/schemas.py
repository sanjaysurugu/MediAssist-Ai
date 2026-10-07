from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SymptomCheckRequest(BaseModel):
    symptoms: str = Field(..., min_length=5, description="Description of symptoms experienced")
    duration_days: Optional[int] = Field(None, ge=0, description="Duration of symptoms in days")
    age: Optional[int] = Field(None, ge=0, le=120, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    existing_conditions: Optional[List[str]] = Field([], description="Pre-existing medical conditions")


class MedicalConditionConcern(BaseModel):
    condition_name: str
    description: str
    match_confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_specialty: str
    educational_summary: str


class SymptomCheckResponse(BaseModel):
    is_emergency: bool
    priority_level: str = Field(..., description="EMERGENCY, HIGH, MODERATE, LOW")
    summary: str
    detected_symptoms: List[str]
    possible_areas_of_concern: List[MedicalConditionConcern]
    recommended_next_steps: List[str]
    suggested_department: Optional[str] = None
    urgency_recommendation: str
    disclaimer: str

    model_config = ConfigDict(from_attributes=True)
