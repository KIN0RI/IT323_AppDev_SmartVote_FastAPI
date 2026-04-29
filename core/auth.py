from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib
import base64
import os
import hmac
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from models.voter import Voter

SECRET_KEY                = "smartvote-fastapi-secret-key-change-in-production"
ALGORITHM                 = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

bearer = HTTPBearer()

DJANGO_ITERATIONS = 1200000
DJANGO_ALGORITHM  = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    """Hash password using Django's PBKDF2 format so web and mobile share the same hash."""
    salt       = base64.b64encode(os.urandom(16)).decode("utf-8").strip("=")
    dk         = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), DJANGO_ITERATIONS)
    hash_val   = base64.b64encode(dk).decode("utf-8")
    return f"{DJANGO_ALGORITHM}${DJANGO_ITERATIONS}${salt}${hash_val}"


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password against either:
    - Django PBKDF2 hash  (pbkdf2_sha256$...)
    - bcrypt hash         ($2b$... legacy mobile registrations)
    """
    try:
        
        if hashed.startswith("pbkdf2_sha256$"):
            _, iterations, salt, hash_val = hashed.split("$")
            dk = hashlib.pbkdf2_hmac(
                "sha256",
                plain.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            return hmac.compare_digest(
                base64.b64encode(dk).decode("utf-8"),
                hash_val
            )

        
        import bcrypt
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    except Exception:
        return False


def create_access_token(data: dict) -> str:
    payload        = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Voter:
    token = credentials.credentials
    try:
        payload    = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("student_id")
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user = db.query(Voter).filter(Voter.student_id == student_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


def require_admin(current_user: Voter = Depends(get_current_user)) -> Voter:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user