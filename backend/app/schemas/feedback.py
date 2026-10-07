from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PatientFeedbackCreate(BaseModel):
    category: Literal["General feedback", "Suggestion", "Issue"]
    rating: int = Field(..., ge=1, le=5)
    message: str = Field(..., min_length=10, max_length=3000)


class PatientFeedbackOut(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    patient_email: str
    category: str
    rating: int
    message: str
    email_status: Literal["pending", "sent", "failed"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
