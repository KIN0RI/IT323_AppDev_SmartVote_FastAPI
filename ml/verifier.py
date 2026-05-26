"""
Face Verification using Cosine Similarity only.
Compares live webcam face against registered photo.
"""
import os
import base64
import io
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image

from ml.preprocessing import preprocess_image, preprocess_from_file

MODEL_PATH     = "ml/models/face_model.pkl"
LABEL_ENC_PATH = "ml/models/label_encoder.pkl"
THRESHOLD      = 0.55  # cosine similarity threshold


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    model = joblib.load(MODEL_PATH)
    le    = joblib.load(LABEL_ENC_PATH)
    return model, le


def verify_face_svm(
    live_b64:        str,
    student_id:      str,
    registered_path: str,
) -> dict:
    """
    Verify using cosine similarity between live face and registered photo.
    Uses PCA projection if model is available for better comparison.
    """
    return verify_face_similarity(live_b64, registered_path)


def verify_face_similarity(
    live_b64:        str,
    registered_path: str,
    threshold:       float = THRESHOLD,
) -> dict:
    """
    Compare live face vs registered photo using PCA + cosine similarity.
    """
    model, _ = load_model()

    try:
        live_vector = preprocess_image(live_b64)
    except ValueError as e:
        return {
            "verified":   False,
            "confidence": 0.0,
            "method":     "cosine_similarity",
            "message":    str(e),
        }

    try:
        reg_vector = preprocess_from_file(registered_path)
    except ValueError as e:
        return {
            "verified":   False,
            "confidence": 0.0,
            "method":     "cosine_similarity",
            "message":    f"Registered face error: {e}",
        }

    # Use PCA projection if model available — better comparison
    if model is not None:
        pca       = model.named_steps["pca"]
        live_proj = pca.transform(live_vector.reshape(1, -1))
        reg_proj  = pca.transform(reg_vector.reshape(1, -1))
    else:
        live_proj = live_vector.reshape(1, -1)
        reg_proj  = reg_vector.reshape(1, -1)

    similarity = float(cosine_similarity(live_proj, reg_proj)[0][0])
    verified   = similarity >= threshold

    return {
        "verified":   verified,
        "confidence": round(similarity, 4),
        "method":     "pca_cosine_similarity",
        "message":    "Identity confirmed." if verified else
                      f"Similarity {similarity:.0%} below threshold {threshold:.0%}.",
    }


def save_registration_face(b64_string: str, student_id: str) -> str:
    """Save voter's face photo during registration."""
    try:
        preprocess_image(b64_string)
    except ValueError as e:
        raise ValueError(f"Cannot save registration photo: {e}")

    if "," in b64_string:
        b64_string = b64_string.split(",")[1]

    img_bytes = base64.b64decode(b64_string)
    img       = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    folder   = f"media/voter_faces/{student_id}"
    os.makedirs(folder, exist_ok=True)

    existing = len([f for f in os.listdir(folder) if f.endswith(".jpg")])
    filepath = f"{folder}/photo_{existing + 1}.jpg"
    img.save(filepath, "JPEG", quality=90)

    return filepath