from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    student_id: str
    email:      EmailStr
    full_name:  str
    password:   str
    course:     Optional[str] = ""
    year_level: Optional[str] = ""


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access:     str
    role:       str
    full_name:  str
    student_id: str


class ProfileResponse(BaseModel):
    id:           int
    student_id:   str
    email:        str
    full_name:    str
    course:       str
    year_level:   str
    role:         str
    has_voted:    bool
    face_verified: bool

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_name:  Optional[str] = None
    email:      Optional[str] = None
    course:     Optional[str] = None
    year_level: Optional[str] = None



class CandidateResponse(BaseModel):
    id:         int
    name:       str
    position:   str
    course:     str
    year_level: str
    bio:        str
    vote_count: int

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    name:       str
    position:   str
    course:     Optional[str] = ""
    year_level: Optional[str] = ""
    bio:        Optional[str] = ""


class VoteRequest(BaseModel):
    candidate: int


class VoteResponse(BaseModel):
    id:             int
    candidate:      int
    candidate_name: str
    position:       str
    timestamp:      datetime

    class Config:
        from_attributes = True



class VoterLogResponse(BaseModel):
    id:         int
    name:       str
    student_id: str
    email:      str
    login_time: Optional[datetime]
    status:     str
    ip_address: Optional[str]



class ElectionSettingsResponse(BaseModel):
    id:                       int
    title:                    str
    status:                   str
    allow_multiple_votes:     bool
    require_face_verification: bool
    start_date:               Optional[datetime]
    end_date:                 Optional[datetime]

    class Config:
        from_attributes = True


class ElectionSettingsUpdate(BaseModel):
    title:                    Optional[str]      = None
    status:                   Optional[str]      = None
    start_date:               Optional[datetime] = None
    end_date:                 Optional[datetime] = None
    allow_multiple_votes:     Optional[bool]     = None
    require_face_verification: Optional[bool]   = None



class DashboardResponse(BaseModel):
    total_voters:             int
    votes_cast:               int
    remaining_voters:         int
    turnout_percent:          float
    election_status:          str
    candidates_by_position:   dict
