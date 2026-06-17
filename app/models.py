import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean,
    Text, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    REGULATOR = "regulator"
    VERIFIER = "verifier"
    MERCHANT = "merchant"


class ScaleStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCRAPPED = "scrapped"


class AppointmentType(str, enum.Enum):
    ON_SITE = "on_site"
    CENTRALIZED = "centralized"


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class VerificationStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    RECTIFICATION = "rectification"
    REINSPECTION_PASSED = "reinspection_passed"
    REINSPECTION_FAILED = "reinspection_failed"


class LabelStatus(str, enum.Enum):
    ACTIVE = "active"
    VOID = "void"
    EXPIRED = "expired"
    LOST = "lost"


class InspectionType(str, enum.Enum):
    ROUTINE = "routine"
    COMPLAINT = "complaint"
    RANDOM = "random"
    SPECIAL = "special"


class OperationType(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VOID = "void"
    APPROVE = "approve"
    REJECT = "reject"
    OFFLINE_SYNC = "offline_sync"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    merchant = relationship("Merchant", back_populates="users")


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    merchant_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    contact_person = Column(String(50))
    contact_phone = Column(String(20))
    business_type = Column(String(100))
    license_number = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remarks = Column(Text)

    scales = relationship("Scale", back_populates="merchant")
    users = relationship("User", back_populates="merchant")
    appointments = relationship("Appointment", back_populates="merchant")


class Scale(Base):
    __tablename__ = "scales"

    id = Column(Integer, primary_key=True, index=True)
    scale_number = Column(String(50), unique=True, index=True, nullable=False)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)
    scale_type = Column(String(100))
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    max_capacity = Column(Float)
    min_capacity = Column(Float)
    accuracy_class = Column(String(20))
    verification_interval_months = Column(Integer, default=12)
    last_verification_date = Column(Date)
    next_verification_date = Column(Date)
    status = Column(Enum(ScaleStatus), default=ScaleStatus.ACTIVE)
    installation_location = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remarks = Column(Text)

    merchant = relationship("Merchant", back_populates="scales")
    appointments = relationship("Appointment", back_populates="scale")
    verifications = relationship("Verification", back_populates="scale")
    labels = relationship("VerificationLabel", back_populates="scale")
    inspections = relationship("Inspection", back_populates="scale")


class StandardWeight(Base):
    __tablename__ = "standard_weights"

    id = Column(Integer, primary_key=True, index=True)
    weight_code = Column(String(50), unique=True, index=True, nullable=False)
    nominal_value = Column(Float, nullable=False)
    unit = Column(String(10), default="kg")
    accuracy_class = Column(String(20))
    calibration_date = Column(Date)
    calibration_certificate = Column(String(200))
    next_calibration_date = Column(Date)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_no = Column(String(50), unique=True, index=True, nullable=False)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)
    scale_id = Column(Integer, ForeignKey("scales.id"), nullable=False)
    appointment_type = Column(Enum(AppointmentType), nullable=False)
    appointment_date = Column(Date, nullable=False)
    time_slot = Column(String(50))
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    created_by = Column(Integer, ForeignKey("users.id"))
    verifier_id = Column(Integer, ForeignKey("users.id"))
    is_repeat = Column(Boolean, default=False)
    repeat_reason = Column(String(500))
    location = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remarks = Column(Text)

    merchant = relationship("Merchant", back_populates="appointments")
    scale = relationship("Scale", back_populates="appointments")
    verifications = relationship("Verification", back_populates="appointment")


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    verification_no = Column(String(50), unique=True, index=True, nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    scale_id = Column(Integer, ForeignKey("scales.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(VerificationStatus), default=VerificationStatus.NOT_STARTED)
    verification_date = Column(Date, default=date.today)
    environment_temperature = Column(Float)
    environment_humidity = Column(Float)
    environment_other = Column(JSON)
    site_photo_url = Column(String(500))
    seal_info = Column(JSON)
    seal_intact = Column(Boolean)
    is_offline_record = Column(Boolean, default=False)
    offline_sync_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    final_verdict = Column(Text)
    verdict_reason = Column(Text)
    remarks = Column(Text)

    appointment = relationship("Appointment", back_populates="verifications")
    scale = relationship("Scale", back_populates="verifications")
    readings = relationship("VerificationReading", back_populates="verification")
    label = relationship("VerificationLabel", back_populates="verification", uselist=False)
    rectifications = relationship("Rectification", back_populates="verification")


class VerificationReading(Base):
    __tablename__ = "verification_readings"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False)
    standard_weight_id = Column(Integer, ForeignKey("standard_weights.id"))
    load_point = Column(String(50))
    nominal_weight = Column(Float, nullable=False)
    indication_value = Column(Float, nullable=False)
    error = Column(Float)
    error_percentage = Column(Float)
    tolerance = Column(Float)
    is_within_tolerance = Column(Boolean)
    weighing_direction = Column(String(20))
    sequence = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)

    verification = relationship("Verification", back_populates="readings")


class VerificationLabel(Base):
    __tablename__ = "verification_labels"

    id = Column(Integer, primary_key=True, index=True)
    label_number = Column(String(50), unique=True, index=True, nullable=False)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False)
    scale_id = Column(Integer, ForeignKey("scales.id"), nullable=False)
    status = Column(Enum(LabelStatus), default=LabelStatus.ACTIVE)
    issue_date = Column(Date, default=date.today)
    expiry_date = Column(Date)
    issued_by = Column(Integer, ForeignKey("users.id"))
    void_reason = Column(String(500))
    void_date = Column(Date)
    void_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remarks = Column(Text)

    verification = relationship("Verification", back_populates="label")
    scale = relationship("Scale", back_populates="labels")


class Rectification(Base):
    __tablename__ = "rectifications"

    id = Column(Integer, primary_key=True, index=True)
    rectification_no = Column(String(50), unique=True, index=True, nullable=False)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False)
    issue_date = Column(Date, default=date.today)
    deadline = Column(Date)
    issue_description = Column(Text, nullable=False)
    rectification_status = Column(String(50), default="pending")
    rectification_measures = Column(Text)
    rectification_date = Column(Date)
    is_reinspection_needed = Column(Boolean, default=True)
    reinspection_appointment_id = Column(Integer, ForeignKey("appointments.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remarks = Column(Text)

    verification = relationship("Verification", back_populates="rectifications")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_no = Column(String(50), unique=True, index=True, nullable=False)
    scale_id = Column(Integer, ForeignKey("scales.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    inspection_type = Column(Enum(InspectionType), nullable=False)
    inspection_date = Column(Date, default=date.today)
    inspector_id = Column(Integer, ForeignKey("users.id"))
    result = Column(String(50))
    findings = Column(Text)
    related_verification_id = Column(Integer, ForeignKey("verifications.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)

    scale = relationship("Scale", back_populates="inspections")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    operation_type = Column(Enum(OperationType), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)
