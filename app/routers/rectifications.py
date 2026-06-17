from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, crud, crud_verification
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/rectifications", tags=["整改复检"])


@router.get("", response_model=List[schemas.RectificationResponse])
def list_rectifications(
    skip: int = 0,
    limit: int = 100,
    verification_id: int = None,
    rectification_status: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    rectifications = crud_verification.get_rectifications(
        db, skip=skip, limit=limit, verification_id=verification_id,
        rectification_status=rectification_status
    )
    return rectifications


@router.post("", response_model=schemas.RectificationResponse)
def create_rectification(
    rectification: schemas.RectificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    verification = crud_verification.get_verification(db, verification_id=rectification.verification_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status != models.VerificationStatus.FAILED:
        raise HTTPException(status_code=400, detail="Can only create rectification for failed verification")
    
    db_rectification = crud_verification.create_rectification(db, rectification=rectification)
    
    verification.status = models.VerificationStatus.RECTIFICATION
    db.commit()
    
    return db_rectification


@router.get("/{rectification_id}", response_model=schemas.RectificationResponse)
def get_rectification(
    rectification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_rectification = crud_verification.get_rectification(db, rectification_id=rectification_id)
    if db_rectification is None:
        raise HTTPException(status_code=404, detail="Rectification not found")
    return db_rectification


@router.put("/{rectification_id}", response_model=schemas.RectificationResponse)
def update_rectification(
    rectification_id: int,
    rectification_update: schemas.RectificationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_rectification = crud_verification.update_rectification(
        db, rectification_id=rectification_id,
        rectification_update=rectification_update
    )
    if db_rectification is None:
        raise HTTPException(status_code=404, detail="Rectification not found")
    return db_rectification


@router.post("/{rectification_id}/submit", response_model=schemas.RectificationResponse)
def submit_rectification(
    rectification_id: int,
    measures: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.MERCHANT, models.UserRole.ADMIN))
):
    db_rectification = crud_verification.get_rectification(db, rectification_id=rectification_id)
    if not db_rectification:
        raise HTTPException(status_code=404, detail="Rectification not found")
    
    if db_rectification.rectification_status == "completed":
        raise HTTPException(status_code=400, detail="Rectification already submitted")
    
    from datetime import date
    db_rectification.rectification_measures = measures
    db_rectification.rectification_date = date.today()
    db_rectification.rectification_status = "submitted"
    
    db.commit()
    db.refresh(db_rectification)
    return db_rectification


@router.post("/{rectification_id}/reinspection")
def create_reinspection_appointment(
    rectification_id: int,
    appointment_data: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_rectification = crud_verification.get_rectification(db, rectification_id=rectification_id)
    if not db_rectification:
        raise HTTPException(status_code=404, detail="Rectification not found")
    
    if not db_rectification.is_reinspection_needed:
        raise HTTPException(status_code=400, detail="Reinspection not required")
    
    if db_rectification.reinspection_appointment_id:
        existing = crud.get_appointment(db, appointment_id=db_rectification.reinspection_appointment_id)
        if existing and existing.status not in [
            models.AppointmentStatus.COMPLETED,
            models.AppointmentStatus.CANCELLED
        ]:
            raise HTTPException(status_code=400, detail="Reinspection appointment already exists")
    
    appointment = crud.create_appointment(
        db, appointment=appointment_data, created_by=current_user.id,
        is_repeat=True, repeat_reason="整改复检"
    )
    
    db_rectification.reinspection_appointment_id = appointment.id
    db_rectification.rectification_status = "reinspection_scheduled"
    db.commit()
    db.refresh(db_rectification)
    
    return appointment


@router.post("/{rectification_id}/complete")
def complete_rectification(
    rectification_id: int,
    passed: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_rectification = crud_verification.get_rectification(db, rectification_id=rectification_id)
    if not db_rectification:
        raise HTTPException(status_code=404, detail="Rectification not found")
    
    db_rectification.rectification_status = "completed"
    
    verification = db_rectification.verification
    if verification:
        if passed:
            verification.status = models.VerificationStatus.REINSPECTION_PASSED
        else:
            verification.status = models.VerificationStatus.REINSPECTION_FAILED
    
    db.commit()
    db.refresh(db_rectification)
    
    return {
        "rectification": db_rectification,
        "verification_status": verification.status if verification else None
    }
