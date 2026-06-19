from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas, crud, crud_verification
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/labels", tags=["合格标签"])


class LabelCreateWithVoidReason(schemas.VerificationLabelCreate):
    void_reason_category: Optional[models.VoidReason] = models.VoidReason.OTHER
    void_old_reason: Optional[str] = None


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
    label: LabelCreateWithVoidReason,
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

    void_category = label.void_reason_category
    void_reason = label.void_old_reason

    if existing_active and not void_reason:
        latest_verification = None
        if existing_active[0].verification:
            latest_verification = existing_active[0].verification
        if latest_verification and latest_verification.id == label.verification_id:
            void_category = models.VoidReason.VERIFIER_MISTAKE
            void_reason = "检定员误操作重复签发同一次检定的标签"
        elif latest_verification and latest_verification.status in [
            models.VerificationStatus.RECTIFICATION,
            models.VerificationStatus.REINSPECTION_PASSED,
            models.VerificationStatus.REINSPECTION_FAILED
        ]:
            void_category = models.VoidReason.RECTIFICATION_REINSPECTION
            void_reason = "整改后重新检定合格，签发新标签"
        else:
            void_category = models.VoidReason.DUPLICATE_APPLICATION
            void_reason = "商户重复申请或新检定完成，旧标签自动作废"

    label_data = schemas.VerificationLabelCreate(
        verification_id=label.verification_id,
        scale_id=label.scale_id,
        expiry_date=label.expiry_date,
        remarks=label.remarks
    )

    db_label = crud_verification.create_label(
        db,
        label=label_data,
        issued_by=current_user.id,
        void_reason_category=void_category,
        void_old_reason=void_reason
    )

    voided_labels = getattr(db_label, '_voided_old_labels', [])
    for old in voided_labels:
        crud_verification.create_operation_log(
            db,
            user_id=current_user.id,
            operation_type=models.OperationType.VOID,
            entity_type="label",
            entity_id=old.id,
            old_value={"status": "active"},
            new_value={
                "status": "void",
                "void_reason_category": old.void_reason_category.value if old.void_reason_category else None,
                "void_reason": old.void_reason
            },
            remarks=f"签发新标签自动作废：{old.void_reason}"
        )
    
    crud_verification.create_operation_log(
        db,
        user_id=current_user.id,
        operation_type=models.OperationType.CREATE,
        entity_type="label",
        entity_id=db_label.id,
        new_value={
            "label_number": db_label.label_number,
            "scale_id": label.scale_id,
            "voided_previous_count": len(voided_labels)
        },
        remarks=f"签发合格标签，自动作废旧标签 {len(voided_labels)} 个"
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
    void_data: schemas.LabelVoidRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN, models.UserRole.VERIFIER))
):
    db_label = crud_verification.get_label(db, label_id=label_id)
    if not db_label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    if db_label.status != models.LabelStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Only active labels can be voided")
    
    voided = crud_verification.void_label(
        db,
        label_id=label_id,
        void_reason_category=void_data.void_reason_category,
        void_reason=void_data.void_reason,
        void_by=current_user.id,
        notify_regulator=void_data.notify_regulator,
        regulator_notifier_id=current_user.id
    )
    
    crud_verification.create_operation_log(
        db,
        user_id=current_user.id,
        operation_type=models.OperationType.VOID,
        entity_type="label",
        entity_id=label_id,
        old_value={"status": "active"},
        new_value={
            "status": "void",
            "void_reason_category": void_data.void_reason_category.value,
            "void_reason": void_data.void_reason,
            "regulator_notified": void_data.notify_regulator
        },
        remarks=f"手动作废标签：{void_data.void_reason}"
    )
    
    return voided


@router.post("/{label_id}/notify-regulator", response_model=schemas.VerificationLabelResponse)
def notify_regulator_for_void_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_label = crud_verification.get_label(db, label_id=label_id)
    if not db_label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    if db_label.status != models.LabelStatus.VOID:
        raise HTTPException(status_code=400, detail="Only voided labels can mark regulator notification")
    
    if db_label.regulator_notified:
        raise HTTPException(status_code=400, detail="Regulator already notified for this label")
    
    updated = crud_verification.mark_label_regulator_notified(
        db, label_id=label_id, notified_by=current_user.id
    )
    
    crud_verification.create_operation_log(
        db,
        user_id=current_user.id,
        operation_type=models.OperationType.APPROVE,
        entity_type="label",
        entity_id=label_id,
        new_value={"regulator_notified": True},
        remarks="已通知监管人员标签作废情况"
    )
    
    return updated


@router.get("/scale/{scale_id}/active")
def get_active_label_for_scale(
    scale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scale = crud.get_scale(db, scale_id=scale_id)
    if not scale:
        raise HTTPException(status_code=404, detail="Scale not found")
    
    active_labels = crud_verification.get_labels(db, scale_id=scale_id, status=models.LabelStatus.ACTIVE)
    
    return {
        "scale_id": scale_id,
        "has_active_label": len(active_labels) > 0,
        "active_label": active_labels[0] if active_labels else None,
        "active_label_count": len(active_labels)
    }
