from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, elections
from routers import face as face_router

app = FastAPI(
    title       = "USTP SmartVote API (FastAPI)",
    description = "FastAPI backend for the SmartVote mobile application",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(elections.router)
app.include_router(face_router.router)

@app.get("/")
def root():
    return {
        "message": "USTP SmartVote FastAPI Backend",
        "docs":    "http://localhost:8001/docs",
        "status":  "running",
    }