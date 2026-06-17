from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import get_password_hash
from app.utils import generate_no
from typing import Optional, List


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        phone=user.phone,
        merchant_id=user.merchant_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_merchant(db: Session, merchant_id: int) -> Optional[models.Merchant]:
    return db.query(models.Merchant).filter(models.Merchant.id == merchant_id).first()


def get_merchant_by_code(db: Session, merchant_code: str) -> Optional[models.Merchant]:
    return db.query(models.Merchant).filter(models.Merchant.merchant_code == merchant_code).first()


def get_merchants(db: Session, skip: int = 0, limit: int = 100, is_active: bool = None) -> List[models.Merchant]:
    query = db.query(models.Merchant)
    if is_active is not None:
        query = query.filter(models.Merchant.is_active == is_active)
    return query.offset(skip).limit(limit).all()


def create_merchant(db: Session, merchant: schemas.MerchantCreate) -> models.Merchant:
    db_merchant = models.Merchant(**merchant.model_dump())
    db.add(db_merchant)
    db.commit()
    db.refresh(db_merchant)
    return db_merchant


def update_merchant(db: Session, merchant_id: int, merchant_update: schemas.MerchantUpdate) -> Optional[models.Merchant]:
    db_merchant = get_merchant(db, merchant_id)
    if not db_merchant:
        return None
    update_data = merchant_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_merchant, key, value)
    db.commit()
    db.refresh(db_merchant)
    return db_merchant


def get_scale(db: Session, scale_id: int) -> Optional[models.Scale]:
    return db.query(models.Scale).filter(models.Scale.id == scale_id).first()


def get_scale_by_number(db: Session, scale_number: str) -> Optional[models.Scale]:
    return db.query(models.Scale).filter(models.Scale.scale_number == scale_number).first()


def get_scales(
    db: Session, skip: int = 0, limit: int = 100,
    merchant_id: int = None, status: models.ScaleStatus = None
) -> List[models.Scale]:
    query = db.query(models.Scale)
    if merchant_id:
        query = query.filter(models.Scale.merchant_id == merchant_id)
    if status:
        query = query.filter(models.Scale.status == status)
    return query.offset(skip).limit(limit).all()


def create_scale(db: Session, scale: schemas.ScaleCreate) -> models.Scale:
    db_scale = models.Scale(**scale.model_dump())
    db.add(db_scale)
    db.commit()
    db.refresh(db_scale)
    return db_scale


def update_scale(db: Session, scale_id: int, scale_update: schemas.ScaleUpdate) -> Optional[models.Scale]:
    db_scale = get_scale(db, scale_id)
    if not db_scale:
        return None
    update_data = scale_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scale, key, value)
    db.commit()
    db.refresh(db_scale)
    return db_scale


def get_standard_weight(db: Session, weight_id: int) -> Optional[models.StandardWeight]:
    return db.query(models.StandardWeight).filter(models.StandardWeight.id == weight_id).first()


def get_standard_weight_by_code(db: Session, weight_code: str) -> Optional[models.StandardWeight]:
    return db.query(models.StandardWeight).filter(models.StandardWeight.weight_code == weight_code).first()


def get_standard_weights(
    db: Session, skip: int = 0, limit: int = 100, is_available: bool = None
) -> List[models.StandardWeight]:
    query = db.query(models.StandardWeight)
    if is_available is not None:
        query = query.filter(models.StandardWeight.is_available == is_available)
    return query.offset(skip).limit(limit).all()


def create_standard_weight(db: Session, weight: schemas.StandardWeightCreate) -> models.StandardWeight:
    db_weight = models.StandardWeight(**weight.model_dump())
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight


def update_standard_weight(db: Session, weight_id: int, weight_update: schemas.StandardWeightUpdate) -> Optional[models.StandardWeight]:
    db_weight = get_standard_weight(db, weight_id)
    if not db_weight:
        return None
    update_data = weight_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_weight, key, value)
    db.commit()
    db.refresh(db_weight)
    return db_weight


def get_appointment(db: Session, appointment_id: int) -> Optional[models.Appointment]:
    return db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()


def get_appointment_by_no(db: Session, appointment_no: str) -> Optional[models.Appointment]:
    return db.query(models.Appointment).filter(models.Appointment.appointment_no == appointment_no).first()


def get_appointments(
    db: Session, skip: int = 0, limit: int = 100,
    merchant_id: int = None, scale_id: int = None,
    status: models.AppointmentStatus = None, verifier_id: int = None
) -> List[models.Appointment]:
    query = db.query(models.Appointment)
    if merchant_id:
        query = query.filter(models.Appointment.merchant_id == merchant_id)
    if scale_id:
        query = query.filter(models.Appointment.scale_id == scale_id)
    if status:
        query = query.filter(models.Appointment.status == status)
    if verifier_id:
        query = query.filter(models.Appointment.verifier_id == verifier_id)
    return query.order_by(models.Appointment.appointment_date.desc()).offset(skip).limit(limit).all()


def create_appointment(
    db: Session, appointment: schemas.AppointmentCreate,
    created_by: int = None, is_repeat: bool = False, repeat_reason: str = None
) -> models.Appointment:
    appointment_no = generate_no("APPT")
    db_appointment = models.Appointment(
        **appointment.model_dump(),
        appointment_no=appointment_no,
        created_by=created_by,
        is_repeat=is_repeat,
        repeat_reason=repeat_reason,
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def update_appointment(db: Session, appointment_id: int, appointment_update: schemas.AppointmentUpdate) -> Optional[models.Appointment]:
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
    update_data = appointment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def has_pending_appointment(db: Session, scale_id: int) -> bool:
    pending_statuses = [
        models.AppointmentStatus.PENDING,
        models.AppointmentStatus.CONFIRMED,
        models.AppointmentStatus.IN_PROGRESS,
    ]
    count = db.query(models.Appointment).filter(
        models.Appointment.scale_id == scale_id,
        models.Appointment.status.in_(pending_statuses)
    ).count()
    return count > 0
