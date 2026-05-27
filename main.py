from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from routers import auth, elections, face
from core.database import Base, engine, SessionLocal
from core.auth import hash_password
import models.voter
import models.elections
from models.voter import Voter

Base.metadata.create_all(bind=engine)

def seed_admin():
    db = SessionLocal()
    try:
        exists = db.query(Voter).filter(Voter.email == "admin@ustp.edu.ph").first()
        if not exists:
            admin = Voter(
                student_id    = "ADMIN-001",
                email         = "admin@ustp.edu.ph",
                full_name     = "System Admin",
                course        = "",
                year_level    = "",
                password      = hash_password("admin1234"),
                role          = "admin",
                is_active     = True,
                is_staff      = True,
                is_superuser  = True,
                has_voted     = False,
                face_verified = False,
                date_joined   = datetime.now(),
                last_login    = None,
            )
            db.add(admin)
            db.commit()
            print("Admin account created: admin@ustp.edu.ph / admin1234")
    finally:
        db.close()

seed_admin()

app = FastAPI(
    title       = "USTP SmartVote API (FastAPI)",
    description = "FastAPI backend with PCA + SVM Face Verification",
    version     = "2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


os.makedirs("media/voter_faces", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth.router)
app.include_router(elections.router)
app.include_router(face.router)


@app.get("/")
def root():
    return {
        "message": "USTP SmartVote FastAPI Backend",
        "docs":    "http://localhost:8001/docs",
        "status":  "running",
        "ml":      "PCA + SVM face verification active",
    }
