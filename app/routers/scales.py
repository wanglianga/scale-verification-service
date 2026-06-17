from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from app.database import get_db
from app import models, schemas, crud
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/scales", tags=["秤具管理"])


@router.get("", response_model=List[schemas.ScaleResponse])
def list_scales(
    skip: int = 0,
    limit: int = 100,
    merchant_id: int = None,
    status: models.ScaleStatus = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    scales = crud.get_scales(db, skip=skip, limit=limit, merchant_id=merchant_id, status=status)
    return scales


@router.post("", response_model=schemas.ScaleResponse)
def create_scale(
    scale: schemas.ScaleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_scale = crud.get_scale_by_number(db, scale_number=scale.scale_number)
    if db_scale:
        raise HTTPException(status_code=400, detail="Scale number already exists")
    
    merchant = crud.get_merchant(db, merchant_id=scale.merchant_id)
    if not merchant:
        raise HTTPException(status_code=400, detail="Merchant not found")
    
    return crud.create_scale(db=db, scale=scale)


@router.get("/{scale_id}", response_model=schemas.ScaleResponse)
def get_scale(
    scale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_scale = crud.get_scale(db, scale_id=scale_id)
    if db_scale is None:
        raise HTTPException(status_code=404, detail="Scale not found")
    return db_scale


@router.put("/{scale_id}", response_model=schemas.ScaleResponse)
def update_scale(
    scale_id: int,
    scale_update: schemas.ScaleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_scale = crud.update_scale(db, scale_id=scale_id, scale_update=scale_update)
    if db_scale is None:
        raise HTTPException(status_code=404, detail="Scale not found")
    return db_scale


@router.get("/number/{scale_number}", response_model=schemas.ScaleResponse)
def get_scale_by_number(
    scale_number: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_scale = crud.get_scale_by_number(db, scale_number=scale_number)
    if db_scale is None:
        raise HTTPException(status_code=404, detail="Scale not found")
    return db_scale


@router.post("/import")
async def import_scales(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    content = await file.read()
    csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
    
    imported = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            scale_data = schemas.ScaleCreate(
                scale_number=row.get('scale_number', '').strip(),
                merchant_id=int(row.get('merchant_id', 0)),
                scale_type=row.get('scale_type', '').strip() or None,
                manufacturer=row.get('manufacturer', '').strip() or None,
                model=row.get('model', '').strip() or None,
                serial_number=row.get('serial_number', '').strip() or None,
                max_capacity=float(row.get('max_capacity', 0)) if row.get('max_capacity') else None,
                min_capacity=float(row.get('min_capacity', 0)) if row.get('min_capacity') else None,
                accuracy_class=row.get('accuracy_class', '').strip() or None,
                verification_interval_months=int(row.get('verification_interval_months', 12)) if row.get('verification_interval_months') else 12,
                installation_location=row.get('installation_location', '').strip() or None,
                remarks=row.get('remarks', '').strip() or None,
            )
            existing = crud.get_scale_by_number(db, scale_number=scale_data.scale_number)
            if not existing:
                crud.create_scale(db, scale=scale_data)
                imported += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    return {
        "imported": imported,
        "errors": errors,
        "total": imported + len(errors)
    }
