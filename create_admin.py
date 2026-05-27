"""
Run this script once to create an admin account.
Usage: python create_admin.py
"""
import os
from datetime import datetime
from core.database import SessionLocal
from core.auth import hash_password
from models.voter import Voter
import models.elections  # ensure all tables exist

from core.database import Base, engine
Base.metadata.create_all(bind=engine)

ADMIN_EMAIL     = "admin@ustp.edu.ph"
ADMIN_PASSWORD  = "admin1234"
ADMIN_NAME      = "System Admin"
ADMIN_STUDENTID = "ADMIN-001"

db = SessionLocal()

existing = db.query(Voter).filter(Voter.email == ADMIN_EMAIL).first()
if existing:
    print(f"Admin already exists: {ADMIN_EMAIL}")
else:
    admin = Voter(
        student_id   = ADMIN_STUDENTID,
        email        = ADMIN_EMAIL,
        full_name    = ADMIN_NAME,
        course       = "",
        year_level   = "",
        password     = hash_password(ADMIN_PASSWORD),
        role         = "admin",
        is_active    = True,
        is_staff     = True,
        is_superuser = True,
        has_voted    = False,
        face_verified = False,
        date_joined  = datetime.now(),
        last_login   = None,
    )
    db.add(admin)
    db.commit()
    print(f"Admin created successfully!")
    print(f"  Email:    {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")

db.close()