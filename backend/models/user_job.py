from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, UniqueConstraint
from datetime import datetime
from database import Base


class UserJob(Base):
    __tablename__ = "user_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=True)
    location_text = Column(String(255), nullable=True)
    country = Column(String(80), nullable=True)
    work_mode = Column(String(30), nullable=True)
    score = Column(Float, nullable=True)
    query = Column(String(255), nullable=True)
    status = Column(String(50), default="none", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job"),
    )
