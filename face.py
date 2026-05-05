"""
STEP 4 — FACE VERIFICATION API ENDPOINTS
==========================================
FastAPI router that exposes the ML pipeline as REST endpoints.

Endpoints:
  POST /api/face/register-face/   — Save voter's face during registration
  POST /api/face/verify/          — Verify voter identity before voting
  POST /api/face/train/           — Retrain the PCA+SVM model (admin only)
  GET  /api/face/status/          — Check if model is trained and ready
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.auth import get_current_user, require_admin
from models.voter import Voter
from ml.verifier import (
    verify_face_svm,
    verify_face_similarity,
    save_registration_face,
)

router = APIRouter(prefix="/api/face", tags=["Face Verification"])

MODEL_PATH = "ml/models/face_model.pkl"


# ── Request/Response schemas ──────────────────────────────────────────────────

class FaceImageRequest(BaseModel):
    image: str   # base64-encoded image from camera


class VerifyRequest(BaseModel):
    image: str   # base64-encoded live face capture


class VerifyResponse(BaseModel):
    verified:   bool
    confidence: float
    method:     str
    message:    str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register-face/")
def register_face(
    payload:      FaceImageRequest,
    current_user: Voter   = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """
    POST /api/face/register-face/

    Saves the voter's face photo during registration.
    Called after the voter fills in their registration form.

    Flow:
      1. Decode base64 image
      2. Detect face (reject if no face found)
      3. Save to media/voter_faces/<student_id>/photo_N.jpg
      4. Update voter's face_photo_path in database
    """
    try:
        saved_path = save_registration_face(
            b64_string = payload.image,
            student_id = current_user.student_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save the path in the database
    current_user.face_photo_path = saved_path
    db.commit()

    return {
        "message":    "Face registered successfully.",
        "photo_path": saved_path,
        "student_id": current_user.student_id,
    }


@router.post("/verify/", response_model=VerifyResponse)
def verify_face(
    payload:      VerifyRequest,
    current_user: Voter   = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """
    POST /api/face/verify/

    Verifies the voter's live face against their registered face.
    Must be called before allowing the voter to cast their vote.

    Flow:
      1. Check voter has a registered face photo
      2. If SVM model trained → use Mode A (SVM identity check)
      3. If no model yet → use Mode B (cosine similarity fallback)
      4. If verified → update face_verified flag in database
    """
    # Check voter has a registered face
    registered_path = getattr(current_user, "face_photo_path", None)

    if not registered_path or not os.path.exists(registered_path):
        raise HTTPException(
            status_code=400,
            detail="No registered face found. Please register your face first."
        )

    # Choose verification mode based on whether model is trained
    if os.path.exists(MODEL_PATH):
        # Mode A — SVM classifier
        result = verify_face_svm(
            live_b64        = payload.image,
            student_id      = current_user.student_id,
            registered_path = registered_path,
        )
    else:
        # Mode B — cosine similarity fallback
        result = verify_face_similarity(
            live_b64        = payload.image,
            registered_path = registered_path,
        )

    # Update face_verified flag in database if successful
    if result["verified"]:
        current_user.face_verified = True
        db.commit()

    return VerifyResponse(
        verified   = result["verified"],
        confidence = result["confidence"],
        method     = result["method"],
        message    = result["message"],
    )


@router.post("/train/")
def train_model(
    current_user: Voter = Depends(require_admin),
):
    """
    POST /api/face/train/  — Admin only

    Retrains the PCA + SVM model using all collected voter face images.
    Run this after enough voters have registered their faces.

    Recommended: train when at least 10+ voters have registered faces.
    """
    from ml.train import train
    try:
        model, le = train()
        n_classes = len(le.classes_)
        return {
            "message":        "Model trained successfully.",
            "voters_trained": n_classes,
            "model_path":     MODEL_PATH,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/status/")
def model_status(current_user: Voter = Depends(get_current_user)):
    """
    GET /api/face/status/

    Returns the current status of the ML model.
    """
    model_exists = os.path.exists(MODEL_PATH)
    mode         = "pca_svm" if model_exists else "cosine_similarity_fallback"

    return {
        "model_trained":    model_exists,
        "model_path":       MODEL_PATH if model_exists else None,
        "verification_mode": mode,
        "message": (
            "PCA + SVM model is ready. Using Mode A (SVM identity check)."
            if model_exists else
            "No trained model yet. Using Mode B (cosine similarity fallback). "
            "Register more voters then call POST /api/face/train/ to train the model."
        ),
    }
