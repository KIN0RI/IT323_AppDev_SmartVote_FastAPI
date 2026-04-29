from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, elections

app = FastAPI(
    title       = "USTP SmartVote API (FastAPI)",
    description = "FastAPI backend for the SmartVote mobile application",
    version     = "1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],  
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(auth.router)
app.include_router(elections.router)


@app.get("/")
def root():
    return {
        "message": "USTP SmartVote FastAPI Backend",
        "docs":    "http://localhost:8001/docs",
        "status":  "running",
    }
