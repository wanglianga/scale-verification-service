from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, crud
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/standard-weights", tags=["标准砝码"])


@router.get("", response_model=List[schemas.StandardWeightResponse])
def list_standard_weights(
    skip: int = 0,
    limit: int = 100,
    is_available: bool = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    weights = crud.get_standard_weights(db, skip=skip, limit=limit, is_available=is_available)
    return weights


@router.post("", response_model=schemas.StandardWeightResponse)
def create_standard_weight(
    weight: schemas.StandardWeightCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN, models.UserRole.VERIFIER))
):
    db_weight = crud.get_standard_weight_by_code(db, weight_code=weight.weight_code)
    if db_weight:
        raise HTTPException(status_code=400, detail="Weight code already exists")
    return crud.create_standard_weight(db=db, weight=weight)


@router.get("/{weight_id}", response_model=schemas.StandardWeightResponse)
def get_standard_weight(
    weight_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_weight = crud.get_standard_weight(db, weight_id=weight_id)
    if db_weight is None:
        raise HTTPException(status_code=404, detail="Standard weight not found")
    return db_weight


@router.put("/{weight_id}", response_model=schemas.StandardWeightResponse)
def update_standard_weight(
    weight_id: int,
    weight_update: schemas.StandardWeightUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.REGULATOR, models.UserRole.ADMIN, models.UserRole.VERIFIER))
):
    db_weight = crud.update_standard_weight(db, weight_id=weight_id, weight_update=weight_update)
    if db_weight is None:
        raise HTTPException(status_code=404, detail="Standard weight not found")
    return db_weight
