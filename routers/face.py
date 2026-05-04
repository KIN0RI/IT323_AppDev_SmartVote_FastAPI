from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from models.voter import Voter
from ml.face_verify import verify_face
from ml.face_verify import enroll_face

router = APIRouter(prefix="/api/face", tags=["Face"])

@router.get("/status/")
def face_status(
    current_user: Voter = Depends(get_current_user),
):
    """Check if voter has a face enrolled."""
    return {"enrolled": current_user.face_encoding is not None}

@router.post("/enroll/")
async def enroll_face_endpoint(
    photo: UploadFile = File(...),
    current_user: Voter = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enroll a face for the current voter."""
    image_bytes = await photo.read()
    encoding = enroll_face(image_bytes)
    current_user.face_encoding = encoding
    db.commit()
    return {"message": "Face enrolled successfully"}

@router.post("/verify/")
async def verify_face_endpoint(
    photo: UploadFile = File(...),
    current_user: Voter = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify face against stored encoding."""
    if not current_user.face_encoding:
        raise HTTPException(status_code=400, detail="No face enrolled. Please enroll first.")
    image_bytes = await photo.read()
    result = verify_face(image_bytes, current_user.face_encoding)
    if result["verified"]:
        current_user.face_verified = True
        db.commit()
    return {
        "verified": result["verified"],
        "confidence": result["confidence"],
        "detail": result["detail"]
    }