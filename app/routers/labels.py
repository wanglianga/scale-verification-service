from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, crud, crud_verification
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/labels", tags=["合格标签"])


@router.get("", response_model=List[schemas.VerificationLabelResponse])
def list_labels(
    skip: int = 0,
    limit: int = 100,
    scale_id: int = None,
    status: models.LabelStatus = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    labels = crud_verification.get_labels(
        db, skip=skip, limit=limit, scale_id=scale_id, status=status
    )
    return labels


@router.post("", response_model=schemas.VerificationLabelResponse)
def create_label(
    label: schemas.VerificationLabelCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.VERIFIER, models.UserRole.ADMIN, models.UserRole.REGULATOR))
):
    verification = crud_verification.get_verification(db, verification_id=label.verification_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status != models.VerificationStatus.PASSED:
        raise HTTPException(status_code=400, detail="Can only issue label for passed verification")
    
    scale = crud.get_scale(db, scale_id=label.scale_id)
    if not scale:
        raise HTTPException(status_code=404, detail="Scale not found")
    
    existing_active = crud_verification.get_labels(db, scale_id=label.scale_id, status=models.LabelStatus.ACTIVE)
    if existing_active:
        raise HTTPException(status_code=400, detail="Scale already has an active label")
    
    db_label = crud_verification.create_label(db, label=label, issued_by=current_user.id)
    
    crud_verification.create_operation_log(
        db,
        user_id=current_user.id,
        operation_type=models.OperationType.CREATE,
        entity_type="label",
        entity_id=db_label.id,
        new_value={"label_number": db_label.label_number, "scale_id": label.scale_id},
        remarks="签发合格标签"
    )
    
    return db_label


@router.get("/{label_id}", response_model=schemas.VerificationLabelResponse)
def get_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_label = crud_verification.get_label(db, label_id=label_id)
    if db_label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    return db_label


@router.get("/number/{label_number}", response_model=schemas.VerificationLabelResponse)
def get_label_by_number(
    label_number: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_label = crud_verification.get_label_by_number(db, label_number=label_number)
    if db_label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    return db_label


@router.post("/{label_id}/void", response_model=schemas.VerificationLabelResponse)
def void_label(
    label_id: int,
    void_reason: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN, models.UserRole.VERIFIER))
):
    db_label = crud_verification.get_label(db, label_id=label_id)
    if not db_label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    if db_label.status != models.LabelStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Only active labels can be voided")
    
    voided = crud_verification.void_label(
        db, label_id=label_id, void_reason=void_reason, void_by=current_user.id
    )
    
    crud_verification.create_operation_log(
        db,
        user_id=current_user.id,
        operation_type=models.OperationType.VOID,
        entity_type="label",
        entity_id=label_id,
        old_value={"status": "active"},
        new_value={"status": "void", "void_reason": void_reason},
        remarks="标签作废"
    )
    
    return voided
