from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from app.database import get_db
from app import models, schemas, crud
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/merchants", tags=["商户管理"])


@router.get("", response_model=List[schemas.MerchantResponse])
def list_merchants(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    merchants = crud.get_merchants(db, skip=skip, limit=limit, is_active=is_active)
    return merchants


@router.post("", response_model=schemas.MerchantResponse)
def create_merchant(
    merchant: schemas.MerchantCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_merchant = crud.get_merchant_by_code(db, merchant_code=merchant.merchant_code)
    if db_merchant:
        raise HTTPException(status_code=400, detail="Merchant code already exists")
    return crud.create_merchant(db=db, merchant=merchant)


@router.get("/{merchant_id}", response_model=schemas.MerchantResponse)
def get_merchant(
    merchant_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_merchant = crud.get_merchant(db, merchant_id=merchant_id)
    if db_merchant is None:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return db_merchant


@router.put("/{merchant_id}", response_model=schemas.MerchantResponse)
def update_merchant(
    merchant_id: int,
    merchant_update: schemas.MerchantUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN))
):
    db_merchant = crud.update_merchant(db, merchant_id=merchant_id, merchant_update=merchant_update)
    if db_merchant is None:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return db_merchant


@router.post("/import")
async def import_merchants(
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
            merchant_data = schemas.MerchantCreate(
                merchant_code=row.get('merchant_code', '').strip(),
                name=row.get('name', '').strip(),
                address=row.get('address', '').strip() or None,
                contact_person=row.get('contact_person', '').strip() or None,
                contact_phone=row.get('contact_phone', '').strip() or None,
                business_type=row.get('business_type', '').strip() or None,
                license_number=row.get('license_number', '').strip() or None,
                remarks=row.get('remarks', '').strip() or None,
            )
            existing = crud.get_merchant_by_code(db, merchant_code=merchant_data.merchant_code)
            if not existing:
                crud.create_merchant(db, merchant=merchant_data)
                imported += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    return {
        "imported": imported,
        "errors": errors,
        "total": imported + len(errors)
    }
