from sqlalchemy.orm import Session
from app import models, schemas
from app.utils import generate_no, calculate_error, calculate_error_percentage, calculate_tolerance, is_within_tolerance
from datetime import date
from typing import Optional, List


def get_verification(db: Session, verification_id: int) -> Optional[models.Verification]:
    return db.query(models.Verification).filter(models.Verification.id == verification_id).first()


def get_verification_by_no(db: Session, verification_no: str) -> Optional[models.Verification]:
    return db.query(models.Verification).filter(models.Verification.verification_no == verification_no).first()


def get_verifications(
    db: Session, skip: int = 0, limit: int = 100,
    scale_id: int = None, status: models.VerificationStatus = None,
    verifier_id: int = None
) -> List[models.Verification]:
    query = db.query(models.Verification)
    if scale_id:
        query = query.filter(models.Verification.scale_id == scale_id)
    if status:
        query = query.filter(models.Verification.status == status)
    if verifier_id:
        query = query.filter(models.Verification.verifier_id == verifier_id)
    return query.order_by(models.Verification.created_at.desc()).offset(skip).limit(limit).all()


def create_verification(
    db: Session, verification: schemas.VerificationCreate,
    verifier_id: int = None
) -> models.Verification:
    verification_no = generate_no("VER")
    db_verification = models.Verification(
        **verification.model_dump(exclude={"readings"}),
        verification_no=verification_no,
        verifier_id=verifier_id,
        status=models.VerificationStatus.IN_PROGRESS,
    )
    db.add(db_verification)
    db.flush()

    for reading_data in verification.readings:
        reading = create_verification_reading(db, db_verification.id, reading_data)

    db.commit()
    db.refresh(db_verification)
    return db_verification


def update_verification(
    db: Session, verification_id: int,
    verification_update: schemas.VerificationUpdate
) -> Optional[models.Verification]:
    db_verification = get_verification(db, verification_id)
    if not db_verification:
        return None
    update_data = verification_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_verification, key, value)
    db.commit()
    db.refresh(db_verification)
    return db_verification


def get_verification_reading(db: Session, reading_id: int) -> Optional[models.VerificationReading]:
    return db.query(models.VerificationReading).filter(models.VerificationReading.id == reading_id).first()


def create_verification_reading(
    db: Session, verification_id: int,
    reading: schemas.VerificationReadingCreate,
    accuracy_class: str = "III"
) -> models.VerificationReading:
    error = calculate_error(reading.nominal_weight, reading.indication_value)
    error_pct = calculate_error_percentage(reading.nominal_weight, error)
    tolerance = calculate_tolerance(reading.nominal_weight, accuracy_class)
    within_tol = is_within_tolerance(error, tolerance)

    db_reading = models.VerificationReading(
        **reading.model_dump(),
        verification_id=verification_id,
        error=error,
        error_percentage=error_pct,
        tolerance=tolerance,
        is_within_tolerance=within_tol,
    )
    db.add(db_reading)
    db.flush()
    return db_reading


def add_verification_reading(
    db: Session, verification_id: int,
    reading: schemas.VerificationReadingCreate
) -> Optional[models.VerificationReading]:
    db_verification = get_verification(db, verification_id)
    if not db_verification:
        return None
    
    accuracy_class = "III"
    if db_verification.scale and db_verification.scale.accuracy_class:
        accuracy_class = db_verification.scale.accuracy_class
    
    db_reading = create_verification_reading(db, verification_id, reading, accuracy_class)
    db.commit()
    db.refresh(db_reading)
    return db_reading


def update_verification_reading(
    db: Session, reading_id: int,
    reading_update: schemas.VerificationReadingUpdate,
    accuracy_class: str = "III"
) -> Optional[models.VerificationReading]:
    db_reading = get_verification_reading(db, reading_id)
    if not db_reading:
        return None
    
    update_data = reading_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reading, key, value)
    
    if "nominal_weight" in update_data or "indication_value" in update_data:
        db_reading.error = calculate_error(db_reading.nominal_weight, db_reading.indication_value)
        db_reading.error_percentage = calculate_error_percentage(db_reading.nominal_weight, db_reading.error)
        db_reading.tolerance = calculate_tolerance(db_reading.nominal_weight, accuracy_class)
        db_reading.is_within_tolerance = is_within_tolerance(db_reading.error, db_reading.tolerance)
    
    db.commit()
    db.refresh(db_reading)
    return db_reading


def evaluate_verification_result(
    db: Session, verification_id: int
) -> dict:
    db_verification = get_verification(db, verification_id)
    if not db_verification:
        return {}
    
    readings = db_verification.readings
    if not readings:
        return {
            "total_readings": 0,
            "passed_readings": 0,
            "failed_readings": 0,
            "max_error": 0,
            "max_error_percentage": 0,
            "overall_pass": False,
            "seal_check": db_verification.seal_intact,
        }
    
    total = len(readings)
    passed = sum(1 for r in readings if r.is_within_tolerance)
    failed = total - passed
    max_error = max(abs(r.error) for r in readings) if readings else 0
    max_error_pct = max(abs(r.error_percentage) for r in readings) if readings else 0
    
    overall_pass = (
        failed == 0 and 
        (db_verification.seal_intact is None or db_verification.seal_intact)
    )
    
    return {
        "total_readings": total,
        "passed_readings": passed,
        "failed_readings": failed,
        "max_error": max_error,
        "max_error_percentage": max_error_pct,
        "overall_pass": overall_pass,
        "seal_check": db_verification.seal_intact,
    }


def get_label(db: Session, label_id: int) -> Optional[models.VerificationLabel]:
    return db.query(models.VerificationLabel).filter(models.VerificationLabel.id == label_id).first()


def get_label_by_number(db: Session, label_number: str) -> Optional[models.VerificationLabel]:
    return db.query(models.VerificationLabel).filter(models.VerificationLabel.label_number == label_number).first()


def get_labels(
    db: Session, skip: int = 0, limit: int = 100,
    scale_id: int = None, status: models.LabelStatus = None
) -> List[models.VerificationLabel]:
    query = db.query(models.VerificationLabel)
    if scale_id:
        query = query.filter(models.VerificationLabel.scale_id == scale_id)
    if status:
        query = query.filter(models.VerificationLabel.status == status)
    return query.order_by(models.VerificationLabel.created_at.desc()).offset(skip).limit(limit).all()


def create_label(
    db: Session, label: schemas.VerificationLabelCreate,
    issued_by: int = None
) -> models.VerificationLabel:
    label_number = generate_no("LBL")
    
    if not label.expiry_date:
        expiry = date.today().replace(year=date.today().year + 1)
    else:
        expiry = label.expiry_date
    
    db_label = models.VerificationLabel(
        **label.model_dump(),
        label_number=label_number,
        issued_by=issued_by,
        expiry_date=expiry,
    )
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label


def void_label(
    db: Session, label_id: int, void_reason: str, void_by: int
) -> Optional[models.VerificationLabel]:
    db_label = get_label(db, label_id)
    if not db_label:
        return None
    db_label.status = models.LabelStatus.VOID
    db_label.void_reason = void_reason
    db_label.void_date = date.today()
    db_label.void_by = void_by
    db.commit()
    db.refresh(db_label)
    return db_label


def get_rectification(db: Session, rectification_id: int) -> Optional[models.Rectification]:
    return db.query(models.Rectification).filter(models.Rectification.id == rectification_id).first()


def get_rectification_by_no(db: Session, rectification_no: str) -> Optional[models.Rectification]:
    return db.query(models.Rectification).filter(models.Rectification.rectification_no == rectification_no).first()


def get_rectifications(
    db: Session, skip: int = 0, limit: int = 100,
    verification_id: int = None, rectification_status: str = None
) -> List[models.Rectification]:
    query = db.query(models.Rectification)
    if verification_id:
        query = query.filter(models.Rectification.verification_id == verification_id)
    if rectification_status:
        query = query.filter(models.Rectification.rectification_status == rectification_status)
    return query.order_by(models.Rectification.created_at.desc()).offset(skip).limit(limit).all()


def create_rectification(
    db: Session, rectification: schemas.RectificationCreate
) -> models.Rectification:
    rectification_no = generate_no("RECT")
    db_rectification = models.Rectification(
        **rectification.model_dump(),
        rectification_no=rectification_no,
    )
    db.add(db_rectification)
    db.commit()
    db.refresh(db_rectification)
    return db_rectification


def update_rectification(
    db: Session, rectification_id: int,
    rectification_update: schemas.RectificationUpdate
) -> Optional[models.Rectification]:
    db_rectification = get_rectification(db, rectification_id)
    if not db_rectification:
        return None
    update_data = rectification_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rectification, key, value)
    db.commit()
    db.refresh(db_rectification)
    return db_rectification


def get_inspection(db: Session, inspection_id: int) -> Optional[models.Inspection]:
    return db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()


def get_inspection_by_no(db: Session, inspection_no: str) -> Optional[models.Inspection]:
    return db.query(models.Inspection).filter(models.Inspection.inspection_no == inspection_no).first()


def get_inspections(
    db: Session, skip: int = 0, limit: int = 100,
    scale_id: int = None, inspection_type: models.InspectionType = None
) -> List[models.Inspection]:
    query = db.query(models.Inspection)
    if scale_id:
        query = query.filter(models.Inspection.scale_id == scale_id)
    if inspection_type:
        query = query.filter(models.Inspection.inspection_type == inspection_type)
    return query.order_by(models.Inspection.created_at.desc()).offset(skip).limit(limit).all()


def create_inspection(
    db: Session, inspection: schemas.InspectionCreate,
    inspector_id: int = None
) -> models.Inspection:
    inspection_no = generate_no("INSP")
    db_inspection = models.Inspection(
        **inspection.model_dump(),
        inspection_no=inspection_no,
        inspector_id=inspector_id,
    )
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection


def update_inspection(
    db: Session, inspection_id: int,
    inspection_update: schemas.InspectionUpdate
) -> Optional[models.Inspection]:
    db_inspection = get_inspection(db, inspection_id)
    if not db_inspection:
        return None
    update_data = inspection_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inspection, key, value)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection


def create_operation_log(
    db: Session, user_id: int, operation_type: models.OperationType,
    entity_type: str, entity_id: int, old_value: dict = None,
    new_value: dict = None, ip_address: str = None, remarks: str = None
) -> models.OperationLog:
    db_log = models.OperationLog(
        user_id=user_id,
        operation_type=operation_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        remarks=remarks,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_operation_logs(
    db: Session, skip: int = 0, limit: int = 100,
    entity_type: str = None, entity_id: int = None, user_id: int = None
) -> List[models.OperationLog]:
    query = db.query(models.OperationLog)
    if entity_type:
        query = query.filter(models.OperationLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(models.OperationLog.entity_id == entity_id)
    if user_id:
        query = query.filter(models.OperationLog.user_id == user_id)
    return query.order_by(models.OperationLog.created_at.desc()).offset(skip).limit(limit).all()
