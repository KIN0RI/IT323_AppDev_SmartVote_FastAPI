from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class ElectionSettings(Base):
    __tablename__ = "elections_electionsettings"

    id                        = Column(Integer, primary_key=True, index=True)
    title                     = Column(String(200), default="USTP Student Council Election")
    start_date                = Column(DateTime)
    end_date                  = Column(DateTime)
    status                    = Column(String(10), default="upcoming")
    allow_multiple_votes      = Column(Boolean, default=False)
    require_face_verification = Column(Boolean, default=True)
    created_at                = Column(DateTime, server_default=func.now())
    updated_at                = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Candidate(Base):
    __tablename__ = "elections_candidate"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    position    = Column(String(30),  nullable=False)
    course      = Column(String(100), default="")
    year_level  = Column(String(20),  default="")
    bio         = Column(Text, default="")
    photo       = Column(String, nullable=True)
    election_id = Column(Integer, ForeignKey("elections_electionsettings.id"), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())

    votes = relationship("Vote", back_populates="candidate")

    @property
    def vote_count(self):
        return len(self.votes)


class Vote(Base):
    __tablename__ = "elections_vote"

    id           = Column(Integer, primary_key=True, index=True)
    voter_id     = Column(Integer, ForeignKey("accounts_voter.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("elections_candidate.id"), nullable=False)
    position     = Column(String(30), nullable=False)
    timestamp    = Column(DateTime, nullable=False)

    candidate = relationship("Candidate", back_populates="votes")
    voter     = relationship("Voter", foreign_keys=[voter_id])


class VoterLog(Base):
    __tablename__ = "elections_voterlog"

    id         = Column(Integer, primary_key=True, index=True)
    voter_id   = Column(Integer, ForeignKey("accounts_voter.id"), nullable=False)
    login_time = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)

    voter = relationship("Voter", foreign_keys=[voter_id])