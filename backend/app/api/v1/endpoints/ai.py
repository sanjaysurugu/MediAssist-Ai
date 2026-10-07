from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.ai.engine import ai_engine
from app.ai.schemas import SymptomCheckRequest, SymptomCheckResponse
from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, UserRole
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/symptom-check", response_model=SymptomCheckResponse)
def analyze_symptoms_endpoint(
    symptom_in: SymptomCheckRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PATIENT]))
):
    """
    AI Symptom Assistant Endpoint.
    Multi-layer AI educational decision-support pipeline with emergency safety detection.
    """
    response = ai_engine.process_symptoms(symptom_in)

    log_action(
        db=db,
        action="AI_SYMPTOM_CHECK",
        resource="ai_services",
        resource_id=response.priority_level,
        user_id=current_user.id,
        request=request
    )

    return response


@router.get("/emergency-contacts")
def get_emergency_contacts():
    """
    Public Endpoint: Get emergency hotlines and guidance.
    """
    return {
        "emergency_notice": "If you or someone near you is experiencing a medical emergency, call your local emergency services immediately.",
        "contacts": [
            {"region": "United States & Canada", "service": "Emergency Services", "number": "911"},
            {"region": "European Union & UK", "service": "Emergency Services", "number": "112"},
            {"region": "India", "service": "National Emergency Number", "number": "112"},
            {"region": "India", "service": "Ambulance", "number": "102"},
            {"region": "International Suicide Hotline", "service": "Crisis Lifeline", "number": "988"}
        ]
    }
