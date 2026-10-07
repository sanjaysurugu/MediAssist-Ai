from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get("/", response_model=List[AuditLogOut])
def get_audit_logs(
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Retrieve security and compliance audit logs.
    """
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
