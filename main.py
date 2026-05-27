from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from routers import auth, elections, face
from core.database import Base, engine
import models.voter          # register Voter table
import models.elections      # register Candidate, Vote, VoterLog, ElectionSettings tables

# Create all tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

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
