from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from models.user import User
from models.user_job import UserJob
from models.job import Job
from models.password_reset_token import PasswordResetToken

from api.auth import router as auth_router
from api.jobs import router as jobs_router
from api.admin import router as admin_router
from api.ai import router as ai_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(admin_router)
app.include_router(ai_router)