from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services.audit_service import log_action

router = APIRouter()


@router.get("/", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    """
    Public Endpoint: Get a list of all hospital departments.
    """
    return db.query(Department).order_by(Department.name.asc()).all()


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: UUID, db: Session = Depends(get_db)):
    """
    Public Endpoint: Get department details by ID.
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found."
        )
    return department


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Create a new hospital department.
    """
    existing = db.query(Department).filter(Department.name.ilike(dept_in.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department with this name already exists."
        )

    new_dept = Department(**dept_in.model_dump())
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)

    log_action(
        db=db,
        action="DEPARTMENT_CREATE",
        resource="departments",
        resource_id=str(new_dept.id),
        user_id=admin_user.id,
        request=request
    )

    return new_dept


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: UUID,
    dept_in: DepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Update department details.
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found."
        )

    update_data = dept_in.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = db.query(Department).filter(
            Department.name.ilike(update_data["name"]),
            Department.id != department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A department with this name already exists."
            )

    for field, value in update_data.items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)

    log_action(
        db=db,
        action="DEPARTMENT_UPDATE",
        resource="departments",
        resource_id=str(department.id),
        user_id=admin_user.id,
        request=request
    )

    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Delete a department.
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found."
        )

    db.delete(department)
    db.commit()

    log_action(
        db=db,
        action="DEPARTMENT_DELETE",
        resource="departments",
        resource_id=str(department_id),
        user_id=admin_user.id,
        request=request
    )

    return None
