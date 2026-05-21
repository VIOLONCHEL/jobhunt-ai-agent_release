from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.adzuna import search_adzuna
from ai.query_builder import build_query, build_search_queries, choose_alpha
from ai.hybrid_matcher import hybrid_match

from database import get_db
from models.user_job import UserJob
from models.user import User
from security import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class MatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, max_length=20000)
    country: str = "gb"
    page: int = Field(default=1, ge=1)
    results_per_page: int = Field(default=50, ge=1, le=50)
    sort_by: str = "relevance"


class StatusSaveRequest(BaseModel):
    job_id: str
    title: str = ""
    description: str = ""
    source_url: str = ""
    location_text: str = ""
    country: str = ""
    work_mode: str = ""
    score: float = 0.0
    match_percent: float = 0.0
    query: str = ""
    status: str = Field(..., pattern=r"^(none|saved|applied|interview)$")


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(none|saved|applied|interview)$")


def normalize_match_percent(raw_score: float, min_score: float, max_score: float) -> float:
    raw_score = float(raw_score or 0.0)

    if max_score <= min_score:
        return 100.0 if raw_score > 0 else 1.0

    normalized = (raw_score - min_score) / (max_score - min_score)
    percent = 1.0 + normalized * 99.0

    return round(max(1.0, min(100.0, percent)), 1)


def safe_date_key(item: Dict[str, Any]):
    value = item.get("created") or ""

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def get_status_map(db: Session, user_id: int, job_ids: list[str]) -> dict[str, str]:
    if not job_ids:
        return {}

    rows = (
        db.query(UserJob)
        .filter(UserJob.user_id == user_id, UserJob.job_id.in_(job_ids))
        .all()
    )

    return {row.job_id: row.status for row in rows}


def merge_jobs_without_duplicates(job_batches: list[list[dict]]) -> list[dict]:
    merged = {}
    order = []

    for batch in job_batches:
        for job in batch:
            job_id = str(job.get("job_id") or "").strip()

            if not job_id:
                continue

            if job_id not in merged:
                merged[job_id] = job
                order.append(job_id)

    return [merged[job_id] for job_id in order]


@router.post("/match")
def match_jobs(
    payload: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        resume_text = payload.resume_text.strip()

        main_query = build_query(resume_text)
        search_queries = build_search_queries(resume_text)
        alpha = choose_alpha(resume_text)

        job_batches = []
        total_found = 0

        for query in search_queries:
            try:
                adz = search_adzuna(
                    query=query,
                    country=payload.country,
                    page=payload.page,
                    results_per_page=payload.results_per_page,
                    sort_by="relevance",
                )

                jobs = adz.get("jobs", [])
                total_found += int(adz.get("count") or len(jobs))
                job_batches.append(jobs)

            except Exception:
            
                continue

        jobs = merge_jobs_without_duplicates(job_batches)

        if not jobs:
            return {
                "query": main_query,
                "expanded_queries": search_queries,
                "alpha": alpha,
                "total": 0,
                "page": payload.page,
                "results_per_page": payload.results_per_page,
                "results": [],
            }

        job_texts = [
            f"{job.get('title', '')} {job.get('company_name', '')} {job.get('location_text', '')} {job.get('description', '')}"
            for job in jobs
        ]

        ranked_scores = hybrid_match(
            resume_text=resume_text,
            job_texts=job_texts,
            mode="hybrid",
            alpha=alpha,
        )

        score_by_index = {
            item["job_index"]: float(item["score"] or 0.0)
            for item in ranked_scores
        }

        raw_scores = [score_by_index.get(i, 0.0) for i in range(len(jobs))]
        max_score = max(raw_scores) if raw_scores else 0.0
        positive_scores = [s for s in raw_scores if s > 0]
        min_score = min(positive_scores) if positive_scores else 0.0

        for index, job in enumerate(jobs):
            raw_score = float(score_by_index.get(index, 0.0))

            job["score"] = raw_score
            job["match_percent"] = normalize_match_percent(
                raw_score=raw_score,
                min_score=min_score,
                max_score=max_score,
            )

        jobs.sort(key=lambda item: item.get("match_percent", 0.0), reverse=True)

        job_ids = [job.get("job_id") for job in jobs if job.get("job_id")]
        status_map = get_status_map(db, current_user.id, job_ids)

        results = []

        for job in jobs:
            job_id = str(job.get("job_id") or "")

            results.append(
                {
                    "job_id": job_id,
                    "title": job.get("title") or "",
                    "company_name": job.get("company_name") or "",
                    "location_text": job.get("location_text") or "",
                    "country": job.get("country") or "",
                    "created": job.get("created") or "",
                    "description": job.get("description") or "",
                    "source_url": job.get("source_url") or "",
                    "work_mode": job.get("work_mode") or "",
                    "contract_time": job.get("contract_time") or "",
                    "match_percent": job.get("match_percent") or 1.0,
                    "score": job.get("score") or 0.0,
                    "status": status_map.get(job_id, "none"),
                }
            )

        return {
            "query": main_query,
            "expanded_queries": search_queries,
            "alpha": alpha,
            "total": len(results),
            "adzuna_total_found": total_found,
            "page": payload.page,
            "results_per_page": payload.results_per_page,
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/jobs/match crashed: {e}")


@router.post("/status")
def save_status(
    payload: StatusSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        job_id = str(payload.job_id).strip()

        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")

        existing = (
            db.query(UserJob)
            .filter(UserJob.user_id == current_user.id, UserJob.job_id == job_id)
            .first()
        )

        if payload.status == "none":
            if existing:
                db.delete(existing)
                db.commit()

            return {"job_id": job_id, "status": "none"}

        safe_title = (payload.title or "Untitled vacancy").strip()[:255]

        if existing:
            existing.title = safe_title
            existing.description = payload.description or ""
            existing.source_url = payload.source_url or ""
            existing.location_text = payload.location_text or ""
            existing.country = payload.country or ""
            existing.work_mode = payload.work_mode or ""
            existing.score = float(payload.score or 0.0)
            existing.query = payload.query or ""
            existing.status = payload.status
        else:
            existing = UserJob(
                user_id=current_user.id,
                job_id=job_id,
                title=safe_title,
                description=payload.description or "",
                source_url=payload.source_url or "",
                location_text=payload.location_text or "",
                country=payload.country or "",
                work_mode=payload.work_mode or "",
                score=float(payload.score or 0.0),
                query=payload.query or "",
                status=payload.status,
            )

            db.add(existing)

        db.commit()

        return {
            "job_id": job_id,
            "status": payload.status,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"/jobs/status crashed: {e}")


@router.get("/by-status")
def get_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status not in {"saved", "applied", "interview"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    rows: List[UserJob] = (
        db.query(UserJob)
        .filter(UserJob.user_id == current_user.id, UserJob.status == status)
        .all()
    )

    return [
        {
            "job_id": row.job_id,
            "title": row.title,
            "description": row.description or "",
            "source_url": row.source_url or "",
            "location_text": row.location_text or "",
            "country": row.country or "",
            "work_mode": row.work_mode or "",
            "contract_time": "",
            "score": row.score or 0.0,
            "match_percent": round(max(1.0, min(100.0, float(row.score or 0.0) * 100)), 1),
            "status": row.status,
            "company_name": "",
            "created": "",
        }
        for row in rows
    ]