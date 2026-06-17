from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models, schemas, crud
from app.auth import verify_password, create_access_token, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["认证"])

settings = get_settings()


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user)
    )


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
