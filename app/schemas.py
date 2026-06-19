from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models import (
    UserRole, ScaleStatus, AppointmentType, AppointmentStatus,
    VerificationStatus, LabelStatus, InspectionType, OperationType,
    OverToleranceLevel, VoidReason
)


class UserBase(BaseModel):
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    merchant_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    merchant_id: Optional[int] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class MerchantBase(BaseModel):
    merchant_code: str
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    business_type: Optional[str] = None
    license_number: Optional[str] = None
    remarks: Optional[str] = None


class MerchantCreate(MerchantBase):
    pass


class MerchantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    business_type: Optional[str] = None
    license_number: Optional[str] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class MerchantResponse(MerchantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MerchantImportItem(MerchantBase):
    pass


class ScaleBase(BaseModel):
    scale_number: str
    merchant_id: int
    scale_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    max_capacity: Optional[float] = None
    min_capacity: Optional[float] = None
    accuracy_class: Optional[str] = None
    verification_interval_months: Optional[int] = 12
    installation_location: Optional[str] = None
    remarks: Optional[str] = None


class ScaleCreate(ScaleBase):
    pass


class ScaleUpdate(BaseModel):
    merchant_id: Optional[int] = None
    scale_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    max_capacity: Optional[float] = None
    min_capacity: Optional[float] = None
    accuracy_class: Optional[str] = None
    verification_interval_months: Optional[int] = None
    status: Optional[ScaleStatus] = None
    installation_location: Optional[str] = None
    remarks: Optional[str] = None


class ScaleResponse(ScaleBase):
    id: int
    status: ScaleStatus
    last_verification_date: Optional[date] = None
    next_verification_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScaleImportItem(ScaleBase):
    pass


class StandardWeightBase(BaseModel):
    weight_code: str
    nominal_value: float
    unit: str = "kg"
    accuracy_class: Optional[str] = None
    calibration_date: Optional[date] = None
    calibration_certificate: Optional[str] = None
    next_calibration_date: Optional[date] = None
    remarks: Optional[str] = None


class StandardWeightCreate(StandardWeightBase):
    pass


class StandardWeightUpdate(BaseModel):
    nominal_value: Optional[float] = None
    unit: Optional[str] = None
    accuracy_class: Optional[str] = None
    calibration_date: Optional[date] = None
    calibration_certificate: Optional[str] = None
    next_calibration_date: Optional[date] = None
    is_available: Optional[bool] = None
    remarks: Optional[str] = None


class StandardWeightResponse(StandardWeightBase):
    id: int
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    merchant_id: int
    scale_id: int
    appointment_type: AppointmentType
    appointment_date: date
    time_slot: Optional[str] = None
    location: Optional[str] = None
    remarks: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_type: Optional[AppointmentType] = None
    appointment_date: Optional[date] = None
    time_slot: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    verifier_id: Optional[int] = None
    location: Optional[str] = None
    remarks: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    appointment_no: str
    status: AppointmentStatus
    created_by: Optional[int] = None
    verifier_id: Optional[int] = None
    is_repeat: bool
    repeat_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerificationReadingBase(BaseModel):
    standard_weight_id: Optional[int] = None
    load_point: Optional[str] = None
    nominal_weight: float
    indication_value: float
    weighing_direction: Optional[str] = None
    sequence: Optional[int] = 0
    remarks: Optional[str] = None


class VerificationReadingCreate(VerificationReadingBase):
    pass


class VerificationReadingUpdate(BaseModel):
    nominal_weight: Optional[float] = None
    indication_value: Optional[float] = None
    load_point: Optional[str] = None
    remarks: Optional[str] = None


class VerificationReadingResponse(VerificationReadingBase):
    id: int
    verification_id: int
    error: Optional[float] = None
    error_percentage: Optional[float] = None
    tolerance: Optional[float] = None
    is_within_tolerance: Optional[bool] = None
    over_tolerance_level: Optional[OverToleranceLevel] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VerificationBase(BaseModel):
    appointment_id: Optional[int] = None
    scale_id: int
    environment_temperature: Optional[float] = None
    environment_humidity: Optional[float] = None
    environment_other: Optional[dict] = None
    site_photo_url: Optional[str] = None
    seal_info: Optional[dict] = None
    seal_intact: Optional[bool] = None
    is_offline_record: Optional[bool] = False
    final_verdict: Optional[str] = None
    verdict_reason: Optional[str] = None
    remarks: Optional[str] = None


class VerificationCreate(VerificationBase):
    readings: List[VerificationReadingCreate] = []


class VerificationUpdate(BaseModel):
    environment_temperature: Optional[float] = None
    environment_humidity: Optional[float] = None
    environment_other: Optional[dict] = None
    site_photo_url: Optional[str] = None
    seal_info: Optional[dict] = None
    seal_intact: Optional[bool] = None
    status: Optional[VerificationStatus] = None
    final_verdict: Optional[str] = None
    verdict_reason: Optional[str] = None
    remarks: Optional[str] = None


class VerificationResponse(VerificationBase):
    id: int
    verification_no: str
    status: VerificationStatus
    verification_date: date
    verifier_id: Optional[int] = None
    readings: List[VerificationReadingResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerificationLabelBase(BaseModel):
    verification_id: int
    scale_id: int
    expiry_date: Optional[date] = None
    remarks: Optional[str] = None


class VerificationLabelCreate(VerificationLabelBase):
    pass


class VerificationLabelResponse(VerificationLabelBase):
    id: int
    label_number: str
    status: LabelStatus
    issue_date: date
    issued_by: Optional[int] = None
    void_reason_category: Optional[VoidReason] = None
    void_reason: Optional[str] = None
    void_date: Optional[date] = None
    void_time: Optional[datetime] = None
    void_by: Optional[int] = None
    regulator_notified: Optional[bool] = None
    regulator_notified_time: Optional[datetime] = None
    regulator_notified_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LabelVoidRequest(BaseModel):
    void_reason_category: VoidReason
    void_reason: str
    notify_regulator: Optional[bool] = False


class RectificationBase(BaseModel):
    verification_id: int
    issue_description: str
    deadline: Optional[date] = None
    is_reinspection_needed: Optional[bool] = True
    remarks: Optional[str] = None


class RectificationCreate(RectificationBase):
    pass


class RectificationUpdate(BaseModel):
    issue_description: Optional[str] = None
    deadline: Optional[date] = None
    rectification_status: Optional[str] = None
    rectification_measures: Optional[str] = None
    rectification_date: Optional[date] = None
    is_reinspection_needed: Optional[bool] = None
    reinspection_appointment_id: Optional[int] = None
    remarks: Optional[str] = None


class RectificationResponse(RectificationBase):
    id: int
    rectification_no: str
    issue_date: date
    rectification_status: str
    rectification_measures: Optional[str] = None
    rectification_date: Optional[date] = None
    reinspection_appointment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InspectionBase(BaseModel):
    scale_id: int
    merchant_id: Optional[int] = None
    inspection_type: InspectionType
    inspection_date: Optional[date] = None
    result: Optional[str] = None
    findings: Optional[str] = None
    related_verification_id: Optional[int] = None
    remarks: Optional[str] = None


class InspectionCreate(InspectionBase):
    pass


class InspectionUpdate(BaseModel):
    inspection_type: Optional[InspectionType] = None
    inspection_date: Optional[date] = None
    result: Optional[str] = None
    findings: Optional[str] = None
    related_verification_id: Optional[int] = None
    remarks: Optional[str] = None


class InspectionResponse(InspectionBase):
    id: int
    inspection_no: str
    inspector_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    operation_type: OperationType
    entity_type: str
    entity_id: int
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list


class VerificationVerdictRequest(BaseModel):
    final_verdict: str
    verdict_reason: str


class FailedReadingDetail(BaseModel):
    reading_id: int
    load_point: Optional[str] = None
    nominal_weight: float
    indication_value: float
    error: float
    error_percentage: float
    tolerance: float
    over_tolerance_level: OverToleranceLevel
    over_tolerance_ratio: float


class MultiPointEvaluationResponse(BaseModel):
    verification_id: int
    verification_no: str
    scale_id: int
    accuracy_class: Optional[str] = None
    total_readings: int
    passed_readings: int
    failed_readings: int
    max_error: float
    max_error_percentage: float
    overall_pass: bool
    seal_check: Optional[bool] = None
    worst_over_tolerance_level: OverToleranceLevel
    failed_readings_detail: List[FailedReadingDetail] = []
    allow_adjustment: bool
    adjustment_deadline_days: int
    reinspection_deadline_days: int
    rectification_suggestions: List[str] = []
    reinspection_required_load_points: List[str] = []
