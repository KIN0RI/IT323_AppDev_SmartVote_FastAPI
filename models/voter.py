from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func
from core.database import Base


class Voter(Base):
    __tablename__ = "accounts_voter"

    id            = Column(Integer, primary_key=True, index=True)
    student_id    = Column(String(20), unique=True, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    full_name     = Column(String(150), nullable=False)
    course        = Column(String(100), default="")
    year_level    = Column(String(20),  default="")
    role          = Column(String(10),  default="student")
    has_voted     = Column(Boolean, default=False)
    face_verified = Column(Boolean, default=False)
    date_joined   = Column(DateTime, nullable=False)
    last_login    = Column(DateTime, nullable=True)
    is_active     = Column(Boolean, default=True)
    is_staff      = Column(Boolean, default=False)
    is_superuser  = Column(Boolean, default=False)
    password      = Column(String, nullable=False)