from typing import Optional
from uuid import UUID
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_action(
    db: Session,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Service helper to create audit log records for compliance and system tracking.
    """
    ip_address = None
    user_agent = None

    if request:
        # Extract IP address from request (handling proxies if present)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        
        user_agent = request.headers.get("User-Agent")

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
