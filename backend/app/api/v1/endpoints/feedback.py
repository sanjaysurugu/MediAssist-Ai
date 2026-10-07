import logging
import smtplib
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_roles
from app.models.feedback import PatientFeedback as PatientFeedbackModel
from app.models.user import User, UserRole
from app.schemas.feedback import PatientFeedbackCreate, PatientFeedbackOut
from app.services.audit_service import log_action
from app.services.password_reset_service import feedback_email_configured, send_feedback_email
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def submit_patient_feedback(
    feedback_in: PatientFeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PATIENT]))
):
    feedback_record = PatientFeedbackModel(
        patient_id=current_user.id,
        category=feedback_in.category,
        rating=feedback_in.rating,
        message=feedback_in.message,
        email_status="pending"
    )
    db.add(feedback_record)
    db.commit()
    db.refresh(feedback_record)

    if feedback_email_configured():
        try:
            send_feedback_email(
                sender_name=current_user.full_name,
                sender_email=current_user.email,
                category=feedback_in.category,
                rating=feedback_in.rating,
                feedback=feedback_in.message
            )
            feedback_record.email_status = "sent"
            db.commit()
            message = f"Thank you. Your feedback was sent to {settings.FEEDBACK_RECIPIENT_EMAIL}."
        except (OSError, smtplib.SMTPException):
            logger.exception("Unable to deliver patient platform feedback.")
            feedback_record.email_status = "failed"
            db.commit()
            message = "Your feedback was saved, but email delivery failed. The administrator can review it in the dashboard."
    else:
        message = "Your feedback was saved. Email forwarding is not configured yet, but the administrator can review it in the dashboard."

    log_action(
        db=db,
        action="PATIENT_PLATFORM_FEEDBACK",
        resource="platform_feedback",
        resource_id=str(feedback_record.id),
        user_id=current_user.id,
        request=request
    )
    return {"message": message, "email_status": feedback_record.email_status}


@router.get("/", response_model=List[PatientFeedbackOut])
def list_patient_feedback(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    records = db.query(PatientFeedbackModel, User).join(
        User,
        PatientFeedbackModel.patient_id == User.id
    ).order_by(
        PatientFeedbackModel.created_at.desc()
    ).offset(offset).limit(limit).all()
    return [
        PatientFeedbackOut(
            id=feedback.id,
            patient_id=feedback.patient_id,
            patient_name=patient.full_name,
            patient_email=patient.email,
            category=feedback.category,
            rating=feedback.rating,
            message=feedback.message,
            email_status=feedback.email_status,
            created_at=feedback.created_at
        )
        for feedback, patient in records
    ]


@router.post("/{feedback_id}/retry-email")
def retry_feedback_email(
    feedback_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    feedback_record = db.query(PatientFeedbackModel).filter(
        PatientFeedbackModel.id == feedback_id
    ).first()
    if not feedback_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found.")
    if feedback_record.email_status == "sent":
        return {"message": "This feedback has already been emailed.", "email_status": "sent"}
    if not feedback_email_configured():
        return {"email_status": feedback_record.email_status}

    patient = db.query(User).filter(User.id == feedback_record.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback author not found.")
    log_action(
        db=db,
        action="ADMIN_RETRY_FEEDBACK_EMAIL",
        resource="platform_feedback",
        resource_id=str(feedback_record.id),
        user_id=admin_user.id,
        request=request
    )
    try:
        send_feedback_email(
            sender_name=patient.full_name,
            sender_email=patient.email,
            category=feedback_record.category,
            rating=feedback_record.rating,
            feedback=feedback_record.message
        )
    except (OSError, smtplib.SMTPException):
        logger.exception("Unable to retry patient feedback email delivery.")
        feedback_record.email_status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Feedback is still saved, but email delivery failed. Please try again later."
        ) from None

    feedback_record.email_status = "sent"
    db.commit()
    return {
        "message": f"Feedback was emailed to {settings.FEEDBACK_RECIPIENT_EMAIL}.",
        "email_status": "sent"
    }
