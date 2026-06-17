from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, crud_verification
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/operation-logs", tags=["操作日志"])


@router.get("", response_model=List[schemas.OperationLogResponse])
def list_operation_logs(
    skip: int = 0,
    limit: int = 100,
    entity_type: str = None,
    entity_id: int = None,
    user_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN, models.UserRole.REGULATOR))
):
    logs = crud_verification.get_operation_logs(
        db, skip=skip, limit=limit, entity_type=entity_type,
        entity_id=entity_id, user_id=user_id
    )
    return logs
