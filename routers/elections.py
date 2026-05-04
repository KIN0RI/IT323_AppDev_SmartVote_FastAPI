from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from core.auth import get_current_user, require_admin
from models.voter import Voter
from datetime import datetime
from models.elections import Candidate, Vote, VoterLog, ElectionSettings
from schemas.schemas import (
    CandidateResponse, CandidateCreate,
    VoteRequest, VoteResponse,
    VoterLogResponse, DashboardResponse,
    ElectionSettingsResponse, ElectionSettingsUpdate,
)

router = APIRouter(prefix="/api", tags=["Elections"])



@router.get("/candidates/", response_model=List[CandidateResponse])
def list_candidates(
    position: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Voter = Depends(get_current_user),
):
    """GET /api/candidates/"""
    qs = db.query(Candidate)
    if position:
        qs = qs.filter(Candidate.position == position)
    candidates = qs.order_by(Candidate.position, Candidate.name).all()
    return [
        CandidateResponse(
            id=c.id, name=c.name, position=c.position,
            course=c.course, year_level=c.year_level,
            bio=c.bio, vote_count=c.vote_count
        ) for c in candidates
    ]


@router.post("/candidates/", response_model=CandidateResponse, status_code=201)
def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """POST /api/candidates/ — admin only"""
    candidate = Candidate(**payload.model_dump())
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return CandidateResponse(
        id=candidate.id, name=candidate.name, position=candidate.position,
        course=candidate.course, year_level=candidate.year_level,
        bio=candidate.bio, vote_count=0
    )


@router.put("/candidates/{pk}/", response_model=CandidateResponse)
def update_candidate(
    pk: int,
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """PUT /api/candidates/<pk>/"""
    candidate = db.query(Candidate).filter(Candidate.id == pk).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    for key, value in payload.model_dump().items():
        setattr(candidate, key, value)
    db.commit()
    db.refresh(candidate)
    return CandidateResponse(
        id=candidate.id, name=candidate.name, position=candidate.position,
        course=candidate.course, year_level=candidate.year_level,
        bio=candidate.bio, vote_count=candidate.vote_count
    )


@router.delete("/candidates/{pk}/", status_code=204)
def delete_candidate(
    pk: int,
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """DELETE /api/candidates/<pk>/"""
    candidate = db.query(Candidate).filter(Candidate.id == pk).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    db.delete(candidate)
    db.commit()



@router.post("/vote/", status_code=201)
def cast_vote(
    payload: VoteRequest,
    db: Session = Depends(get_db),
    current_user: Voter = Depends(get_current_user),
):
    """POST /api/vote/"""
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Admins cannot vote.")

    if not current_user.face_verified:
        raise HTTPException(status_code=403, detail="Face verification required before voting.")

    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    
    existing = db.query(Vote).filter(
        Vote.voter_id == current_user.id,
        Vote.position == candidate.position
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"You have already voted for {candidate.position}."
        )

    vote = Vote(
    voter_id     = current_user.id,
    candidate_id = candidate.id,
    position     = candidate.position,
    timestamp    = datetime.now(),
)
    db.add(vote)

    
    positions_count = db.query(Candidate.position).distinct().count()
    votes_cast      = db.query(Vote).filter(Vote.voter_id == current_user.id).count() + 1
    if votes_cast >= positions_count:
        current_user.has_voted = True

    db.commit()
    return {"message": f"Vote cast for {candidate.name} ({candidate.position})."}


@router.get("/vote/my/")
def my_votes(
    db: Session = Depends(get_db),
    current_user: Voter = Depends(get_current_user),
):
    """GET /api/vote/my/"""
    votes = db.query(Vote).filter(Vote.voter_id == current_user.id).all()
    return [
        {
            "id":             v.id,
            "candidate":      v.candidate_id,
            "candidate_name": v.candidate.name,
            "position":       v.position,
            "timestamp":      v.timestamp,
        }
        for v in votes
    ]



@router.get("/results/")
def results(db: Session = Depends(get_db)):
    """GET /api/results/ — public"""
    positions  = db.query(Candidate.position).distinct().all()
    data       = {}
    for (pos,) in positions:
        candidates = db.query(Candidate).filter(Candidate.position == pos).all()
        data[pos]  = sorted([
            {
                "id":         c.id,
                "name":       c.name,
                "position":   c.position,
                "course":     c.course,
                "year_level": c.year_level,
                "vote_count": c.vote_count,
            }
            for c in candidates
        ], key=lambda x: x["vote_count"], reverse=True)
    return data



@router.get("/dashboard/")
def dashboard(
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """GET /api/dashboard/ — admin only"""
    total_voters = db.query(Voter).filter(Voter.role == "student").count()
    votes_cast   = db.query(Voter).filter(Voter.role == "student", Voter.has_voted == True).count()
    remaining    = total_voters - votes_cast
    turnout      = round((votes_cast / total_voters * 100), 2) if total_voters else 0.0

    try:
        election  = db.query(ElectionSettings).order_by(ElectionSettings.created_at.desc()).first()
        el_status = election.status if election else "N/A"
    except Exception:
        el_status = "N/A"

    positions = db.query(Candidate.position).distinct().all()
    by_pos    = {}
    for (pos,) in positions:
        candidates = db.query(Candidate).filter(Candidate.position == pos).all()
        by_pos[pos] = sorted([
            {"id": c.id, "name": c.name, "position": c.position, "vote_count": c.vote_count}
            for c in candidates
        ], key=lambda x: x["vote_count"], reverse=True)

    return {
        "total_voters":           total_voters,
        "votes_cast":             votes_cast,
        "remaining_voters":       remaining,
        "turnout_percent":        turnout,
        "election_status":        el_status,
        "candidates_by_position": by_pos,
    }



@router.get("/voter-log/")
def voter_log(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """GET /api/voter-log/ — admin only"""
    students = db.query(Voter).filter(Voter.role == "student")

    if search:
        students = students.filter(
            (Voter.full_name.ilike(f"%{search}%")) |
            (Voter.student_id.ilike(f"%{search}%"))
        )
    if status == "Voted":
        students = students.filter(Voter.has_voted == True)
    elif status == "Pending":
        students = students.filter(Voter.has_voted == False)

    result = []
    for s in students.all():
        last_log = (
            db.query(VoterLog)
            .filter(VoterLog.voter_id == s.id)
            .order_by(VoterLog.login_time.desc())
            .first()
        )
        result.append({
            "id":         s.id,
            "name":       s.full_name,
            "student_id": s.student_id,
            "email":      s.email,
            "login_time": last_log.login_time if last_log else None,
            "status":     "Voted" if s.has_voted else "Pending",
            "ip_address": last_log.ip_address if last_log else None,
        })
    return result



@router.get("/election-settings/", response_model=ElectionSettingsResponse)
def get_election_settings(
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """GET /api/election-settings/"""
    obj = db.query(ElectionSettings).order_by(ElectionSettings.created_at.desc()).first()
    if not obj:
        raise HTTPException(status_code=404, detail="No settings found.")
    return obj


@router.post("/election-settings/", response_model=ElectionSettingsResponse, status_code=201)
def create_election_settings(
    payload: ElectionSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """POST /api/election-settings/"""
    obj = ElectionSettings(**{k: v for k, v in payload.model_dump().items() if v is not None})
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/election-settings/", response_model=ElectionSettingsResponse)
def update_election_settings(
    payload: ElectionSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: Voter = Depends(require_admin),
):
    """PUT /api/election-settings/"""
    obj = db.query(ElectionSettings).order_by(ElectionSettings.created_at.desc()).first()
    if not obj:
        raise HTTPException(status_code=404, detail="No settings found.")
    for key, value in payload.model_dump().items():
        if value is not None:
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj
