from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)
from models.voter import Voter
from models.elections import VoterLog
from schemas.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    ProfileResponse, ProfileUpdate
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register/", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """POST /api/auth/register/"""
    if db.query(Voter).filter(Voter.student_id == payload.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already registered.")
    if db.query(Voter).filter(Voter.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    voter = Voter(
        student_id      = payload.student_id,
        email           = payload.email,
        full_name       = payload.full_name,
        course          = payload.course or "",
        year_level      = payload.year_level or "",
        password = hash_password(payload.password),
        role            = "student",
        is_active       = True,
        is_staff        = False,
        has_voted       = False,
        face_verified   = False,
        date_joined     = datetime.now(),
    )
    db.add(voter)
    db.commit()
    return {"message": "Registration successful. You can now log in."}


@router.post("/login-email/", response_model=TokenResponse)
def login_email(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """POST /api/auth/login-email/"""
    voter = db.query(Voter).filter(Voter.email == payload.email).first()
    if not voter:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(payload.password, voter.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    
    log = VoterLog(
        voter_id   = voter.id,
        ip_address = request.client.host,
        login_time = datetime.now(),
    )
    db.add(log)
    db.commit()

    token = create_access_token({
        "student_id": voter.student_id,
        "role":       voter.role,
        "full_name":  voter.full_name,
    })
    return TokenResponse(
        access     = token,
        role       = voter.role,
        full_name  = voter.full_name,
        student_id = voter.student_id,
    )


@router.get("/profile/", response_model=ProfileResponse)
def get_profile(current_user: Voter = Depends(get_current_user)):
    """GET /api/auth/profile/"""
    return current_user


@router.put("/profile/", response_model=ProfileResponse)
def update_profile(
    payload:      ProfileUpdate,
    current_user: Voter = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """PUT /api/auth/profile/"""
    if payload.full_name:  current_user.full_name  = payload.full_name
    if payload.email:      current_user.email      = payload.email
    if payload.course:     current_user.course     = payload.course
    if payload.year_level: current_user.year_level = payload.year_level
    db.commit()
    db.refresh(current_user)
    return current_user