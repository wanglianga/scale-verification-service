from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app import models, schemas, crud
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/appointments", tags=["检定预约"])


@router.get("", response_model=List[schemas.AppointmentResponse])
def list_appointments(
    skip: int = 0,
    limit: int = 100,
    merchant_id: int = None,
    scale_id: int = None,
    status: models.AppointmentStatus = None,
    verifier_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    appointments = crud.get_appointments(
        db, skip=skip, limit=limit, merchant_id=merchant_id,
        scale_id=scale_id, status=status, verifier_id=verifier_id
    )
    return appointments


@router.post("", response_model=schemas.AppointmentResponse)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scale = crud.get_scale(db, scale_id=appointment.scale_id)
    if not scale:
        raise HTTPException(status_code=404, detail="Scale not found")
    if scale.status != models.ScaleStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Scale is not active")
    
    merchant = crud.get_merchant(db, merchant_id=appointment.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    is_repeat = crud.has_pending_appointment(db, scale_id=appointment.scale_id)
    repeat_reason = None
    if is_repeat:
        repeat_reason = "该秤已有待处理的检定预约"
    
    db_appointment = crud.create_appointment(
        db, appointment=appointment,
        created_by=current_user.id,
        is_repeat=is_repeat,
        repeat_reason=repeat_reason,
    )
    return db_appointment


@router.get("/{appointment_id}", response_model=schemas.AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment


@router.put("/{appointment_id}", response_model=schemas.AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_update: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_appointment = crud.update_appointment(
        db, appointment_id=appointment_id,
        appointment_update=appointment_update
    )
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment


@router.post("/{appointment_id}/cancel", response_model=schemas.AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if db_appointment.status in [models.AppointmentStatus.COMPLETED, models.AppointmentStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot cancel this appointment")
    
    db_appointment.status = models.AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@router.post("/{appointment_id}/confirm", response_model=schemas.AppointmentResponse)
def confirm_appointment(
    appointment_id: int,
    verifier_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.VERIFIER, models.UserRole.ADMIN))
):
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if db_appointment.status != models.AppointmentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending appointments can be confirmed")
    
    if verifier_id:
        db_appointment.verifier_id = verifier_id
    elif current_user.role == models.UserRole.VERIFIER:
        db_appointment.verifier_id = current_user.id
    
    db_appointment.status = models.AppointmentStatus.CONFIRMED
    db.commit()
    db.refresh(db_appointment)
    return db_appointment
