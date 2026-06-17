from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, crud, crud_verification
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/inspections", tags=["监管抽查"])


@router.get("", response_model=List[schemas.InspectionResponse])
def list_inspections(
    skip: int = 0,
    limit: int = 100,
    scale_id: int = None,
    inspection_type: models.InspectionType = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    inspections = crud_verification.get_inspections(
        db, skip=skip, limit=limit, scale_id=scale_id,
        inspection_type=inspection_type
    )
    return inspections


@router.post("", response_model=schemas.InspectionResponse)
def create_inspection(
    inspection: schemas.InspectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    scale = crud.get_scale(db, scale_id=inspection.scale_id)
    if not scale:
        raise HTTPException(status_code=404, detail="Scale not found")
    
    db_inspection = crud_verification.create_inspection(
        db, inspection=inspection, inspector_id=current_user.id
    )
    return db_inspection


@router.get("/{inspection_id}", response_model=schemas.InspectionResponse)
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_inspection = crud_verification.get_inspection(db, inspection_id=inspection_id)
    if db_inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return db_inspection


@router.put("/{inspection_id}", response_model=schemas.InspectionResponse)
def update_inspection(
    inspection_id: int,
    inspection_update: schemas.InspectionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_inspection = crud_verification.update_inspection(
        db, inspection_id=inspection_id,
        inspection_update=inspection_update
    )
    if db_inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return db_inspection


@router.get("/scale/{scale_id}/trace")
def trace_scale_inspections(
    scale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scale = crud.get_scale(db, scale_id=scale_id)
    if not scale:
        raise HTTPException(status_code=404, detail="Scale not found")
    
    inspections = crud_verification.get_inspections(db, scale_id=scale_id)
    verifications = crud_verification.get_verifications(db, scale_id=scale_id)
    labels = crud_verification.get_labels(db, scale_id=scale_id)
    
    return {
        "scale": scale,
        "inspections": inspections,
        "verifications": verifications,
        "labels": labels,
        "total_inspections": len(inspections),
        "total_verifications": len(verifications),
        "active_labels": len([l for l in labels if l.status == models.LabelStatus.ACTIVE])
    }
