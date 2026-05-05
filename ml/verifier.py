"""
STEP 3 — FACE VERIFIER (INFERENCE)
====================================
Loads the trained PCA + SVM model and verifies a live face
against a voter's registered face.

Two verification modes:
  Mode A — Identity check: Is this person voter X?
    → Use the SVM classifier directly.
    → Returns True if SVM predicts the voter's student_id.

  Mode B — Similarity check: How similar are these two faces?
    → Compare PCA projections using cosine similarity.
    → Returns True if similarity >= threshold.
    → Used when no trained model is available yet (fallback).
"""

import os
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

from ml.preprocessing import preprocess_image, preprocess_from_file

MODEL_PATH     = "ml/models/face_model.pkl"
LABEL_ENC_PATH = "ml/models/label_encoder.pkl"

# Similarity threshold for Mode B (0.0 to 1.0)
# Scores >= this value → verified
SIMILARITY_THRESHOLD = 0.75


def load_model():
    """Load the trained PCA + SVM pipeline and label encoder."""
    if not os.path.exists(MODEL_PATH):
        return None, None
    model = joblib.load(MODEL_PATH)
    le    = joblib.load(LABEL_ENC_PATH)
    return model, le


def verify_face_svm(
    live_b64:     str,
    student_id:   str,
    registered_path: str,
) -> dict:
    """
    Mode A — SVM Identity Verification.

    Preprocesses the live face and asks the SVM:
    'Does this face belong to student_id?'

    Args:
        live_b64:        Base64-encoded live camera capture.
        student_id:      The student_id of the voter claiming identity.
        registered_path: File path to the voter's registered face image.

    Returns dict with:
        verified:    bool
        confidence:  float (0.0 to 1.0)
        method:      str
        message:     str
    """
    model, le = load_model()

    # Preprocess live face
    try:
        live_vector = preprocess_image(live_b64)
    except ValueError as e:
        return {
            "verified":   False,
            "confidence": 0.0,
            "method":     "svm",
            "message":    str(e),
        }

    if model is None:
        # No trained model yet — fallback to similarity mode
        return verify_face_similarity(live_b64, registered_path)

    # Get SVM prediction probabilities
    live_vector_2d = live_vector.reshape(1, -1)
    predicted_class = model.predict(live_vector_2d)[0]
    probabilities   = model.predict_proba(live_vector_2d)[0]
    confidence      = float(max(probabilities))

    # Decode the predicted class back to student_id
    predicted_id = le.inverse_transform([predicted_class])[0]
    verified     = (predicted_id == student_id)

    return {
        "verified":      verified,
        "confidence":    round(confidence, 4),
        "predicted_id":  predicted_id,
        "method":        "pca_svm",
        "message":       "Identity confirmed." if verified else "Face does not match registered voter.",
    }


def verify_face_similarity(
    live_b64:        str,
    registered_path: str,
    threshold:       float = SIMILARITY_THRESHOLD,
) -> dict:
    """
    Mode B — PCA Cosine Similarity Verification (fallback).

    Compares the PCA projection of the live face against
    the stored registered face using cosine similarity.

    Used when:
      - The SVM model hasn't been trained yet
      - Only one photo per voter exists

    Args:
        live_b64:        Base64-encoded live camera capture.
        registered_path: File path to voter's registered face.
        threshold:       Minimum cosine similarity to pass (default 0.75).
    """
    model, _ = load_model()

    # Preprocess both images
    try:
        live_vector = preprocess_image(live_b64)
    except ValueError as e:
        return {"verified": False, "confidence": 0.0,
                "method": "similarity", "message": str(e)}

    try:
        reg_vector = preprocess_from_file(registered_path)
    except ValueError as e:
        return {"verified": False, "confidence": 0.0,
                "method": "similarity", "message": f"Registered face error: {e}"}

    # If model exists, project into PCA space first (better accuracy)
    if model is not None:
        pca = model.named_steps["pca"]
        live_proj = pca.transform(live_vector.reshape(1, -1))
        reg_proj  = pca.transform(reg_vector.reshape(1, -1))
    else:
        # Use raw pixel vectors if no PCA model yet
        live_proj = live_vector.reshape(1, -1)
        reg_proj  = reg_vector.reshape(1, -1)

    similarity = float(cosine_similarity(live_proj, reg_proj)[0][0])
    verified   = similarity >= threshold

    return {
        "verified":   verified,
        "confidence": round(similarity, 4),
        "threshold":  threshold,
        "method":     "pca_cosine_similarity",
        "message":    "Identity confirmed." if verified else
                      f"Similarity {similarity:.2f} below threshold {threshold}.",
    }


def save_registration_face(b64_string: str, student_id: str) -> str:
    """
    Save a voter's face image during registration.
    Creates media/voter_faces/<student_id>/ if it doesn't exist.

    Returns the saved file path.
    Raises ValueError if no face detected.
    """
    import base64, io
    from PIL import Image

    # Validate that a face exists in the image before saving
    try:
        preprocess_image(b64_string)   # raises ValueError if no face
    except ValueError as e:
        raise ValueError(f"Cannot save registration photo: {e}")

    # Decode and save the original image
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]

    img_bytes = base64.b64decode(b64_string)
    img       = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    folder    = f"media/voter_faces/{student_id}"
    os.makedirs(folder, exist_ok=True)

    # Count existing photos to number the new one
    existing = len([f for f in os.listdir(folder) if f.endswith(".jpg")])
    filepath = f"{folder}/photo_{existing + 1}.jpg"
    img.save(filepath, "JPEG", quality=90)

    return filepath
