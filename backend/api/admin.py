from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user import User
from models.user_job import UserJob
from security import get_db, require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


class RoleUpdateRequest(BaseModel):
    role: str


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_saved = db.query(func.count(UserJob.id)).filter(UserJob.status == "saved").scalar() or 0
    total_applied = db.query(func.count(UserJob.id)).filter(UserJob.status == "applied").scalar() or 0
    total_interview = db.query(func.count(UserJob.id)).filter(UserJob.status == "interview").scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
    total_regular_users = db.query(func.count(User.id)).filter(User.role == "user").scalar() or 0

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_regular_users": total_regular_users,
        "total_saved": total_saved,
        "total_applied": total_applied,
        "total_interview": total_interview,
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).all()

    result = []
    for user in users:
        job_count = db.query(func.count(UserJob.id)).filter(UserJob.user_id == user.id).scalar() or 0
        result.append({
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "role": user.role,
            "saved_jobs_count": job_count,
        })

    return result


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if payload.role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.role
    db.commit()

    return {"id": user.id, "role": user.role}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(UserJob).filter(UserJob.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    return {"message": "User deleted"}