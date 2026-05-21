from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from models.user import User
from security import (
    get_db,
    hash_password,
    verify_password,
    validate_password_rules,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    nickname: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    nickname: str
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str


class DeleteProfileRequest(BaseModel):
    password: str


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    nickname = payload.nickname.strip()
    email = payload.email.strip().lower()
    password = payload.password.strip()

    if len(nickname) < 2:
        raise HTTPException(status_code=400, detail="Nickname is too short")

    password_errors = validate_password_rules(password)
    if password_errors:
        raise HTTPException(status_code=422, detail=password_errors)

    if db.query(User).filter(User.nickname == nickname).first():
        raise HTTPException(status_code=409, detail="Nickname already taken")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    users_count = db.query(User).count()
    role = "admin" if users_count == 0 else "user"

    user = User(
        nickname=nickname,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "role": user.role,
        },
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    password = payload.password.strip()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "role": user.role,
        },
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "nickname": current_user.nickname,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.put("/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nickname = payload.nickname.strip()
    email = payload.email.strip().lower()

    if len(nickname) < 2:
        raise HTTPException(status_code=400, detail="Nickname is too short")

    existing_nickname = (
        db.query(User)
        .filter(User.nickname == nickname, User.id != current_user.id)
        .first()
    )
    if existing_nickname:
        raise HTTPException(status_code=409, detail="Nickname already taken")

    existing_email = (
        db.query(User)
        .filter(User.email == email, User.id != current_user.id)
        .first()
    )
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    current_user.nickname = nickname
    current_user.email = email

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "nickname": current_user.nickname,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    password_errors = validate_password_rules(payload.new_password)
    if password_errors:
        raise HTTPException(status_code=422, detail=password_errors)

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_profile(
    payload: DeleteProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Password is incorrect")

    db.delete(current_user)
    db.commit()

    return {"message": "Profile deleted"}