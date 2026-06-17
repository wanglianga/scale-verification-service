from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, crud, crud_verification
from app.auth import get_current_user, require_roles
from datetime import date

router = APIRouter(prefix="/verifications", tags=["检定管理"])


@router.get("", response_model=List[schemas.VerificationResponse])
def list_verifications(
    skip: int = 0,
    limit: int = 100,
    scale_id: int = None,
    status: models.VerificationStatus = None,
    verifier_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    verifications = crud_verification.get_verifications(
        db, skip=skip, limit=limit, scale_id=scale_id,
        status=status, verifier_id=verifier_id
    )
    return verifications


@router.post("", response_model=schemas.VerificationResponse)
def create_verification(
    verification: schemas.VerificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN, models.UserRole.REGULATOR))
):
    scale = crud.get_scale(db, scale_id=verification.scale_id)
    if not scale:
        raise HTTPException(status_code=404, detail="Scale not found")
    
    if verification.appointment_id:
        appointment = crud.get_appointment(db, appointment_id=verification.appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if appointment.status == models.AppointmentStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Appointment already completed")
    
    db_verification = crud_verification.create_verification(
        db, verification=verification, verifier_id=current_user.id
    )
    return db_verification


@router.get("/{verification_id}", response_model=schemas.VerificationResponse)
def get_verification(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_verification = crud_verification.get_verification(db, verification_id=verification_id)
    if db_verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return db_verification


@router.put("/{verification_id}", response_model=schemas.VerificationResponse)
def update_verification(
    verification_id: int,
    verification_update: schemas.VerificationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN, models.UserRole.REGULATOR))
):
    db_verification = crud_verification.update_verification(
        db, verification_id=verification_id,
        verification_update=verification_update
    )
    if db_verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return db_verification


@router.post("/{verification_id}/readings", response_model=schemas.VerificationReadingResponse)
def add_reading(
    verification_id: int,
    reading: schemas.VerificationReadingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_verification = crud_verification.get_verification(db, verification_id=verification_id)
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if db_verification.status in [
        models.VerificationStatus.PASSED,
        models.VerificationStatus.FAILED,
        models.VerificationStatus.RECTIFICATION
    ]:
        raise HTTPException(status_code=400, detail="Cannot add readings to completed verification")
    
    db_reading = crud_verification.add_verification_reading(db, verification_id, reading)
    return db_reading


@router.get("/{verification_id}/readings", response_model=List[schemas.VerificationReadingResponse])
def get_readings(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_verification = crud_verification.get_verification(db, verification_id=verification_id)
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    return db_verification.readings


@router.put("/readings/{reading_id}", response_model=schemas.VerificationReadingResponse)
def update_reading(
    reading_id: int,
    reading_update: schemas.VerificationReadingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_reading = crud_verification.get_verification_reading(db, reading_id=reading_id)
    if not db_reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    accuracy_class = "III"
    if db_reading.verification and db_reading.verification.scale:
        if db_reading.verification.scale.accuracy_class:
            accuracy_class = db_reading.verification.scale.accuracy_class
    
    updated = crud_verification.update_verification_reading(
        db, reading_id, reading_update, accuracy_class
    )
    return updated


@router.get("/{verification_id}/evaluate")
def evaluate_verification(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_verification = crud_verification.get_verification(db, verification_id=verification_id)
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    result = crud_verification.evaluate_verification_result(db, verification_id)
    return result


@router.post("/{verification_id}/finalize")
def finalize_verification(
    verification_id: int,
    verdict_data: schemas.VerificationVerdictRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_verification = crud_verification.get_verification(db, verification_id=verification_id)
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if db_verification.status in [
        models.VerificationStatus.PASSED,
        models.VerificationStatus.FAILED,
    ]:
        raise HTTPException(status_code=400, detail="Verification already finalized")
    
    result = crud_verification.evaluate_verification_result(db, verification_id)
    
    if result.get("overall_pass"):
        db_verification.status = models.VerificationStatus.PASSED
    else:
        db_verification.status = models.VerificationStatus.FAILED
    
    db_verification.final_verdict = verdict_data.final_verdict
    db_verification.verdict_reason = verdict_data.verdict_reason
    
    if db_verification.appointment:
        db_verification.appointment.status = models.AppointmentStatus.COMPLETED
    
    scale = db_verification.scale
    if scale:
        scale.last_verification_date = date.today()
        if scale.verification_interval_months:
            from dateutil.relativedelta import relativedelta
            scale.next_verification_date = date.today() + relativedelta(months=scale.verification_interval_months)
    
    db.commit()
    db.refresh(db_verification)
    
    return {
        "verification": db_verification,
        "evaluation": result
    }


@router.post("/{verification_id}/offline-sync")
def sync_offline_verification(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_verification = crud_verification.get_verification(db, verification_id=verification_id)
    if not db_verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    from datetime import datetime
    db_verification.is_offline_record = False
    db_verification.offline_sync_time = datetime.utcnow()
    
    crud_verification.create_operation_log(
        db,
        user_id=current_user.id,
        operation_type=models.OperationType.OFFLINE_SYNC,
        entity_type="verification",
        entity_id=verification_id,
        remarks="离线补录数据同步"
    )
    
    db.commit()
    db.refresh(db_verification)
    return db_verification
