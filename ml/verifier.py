"""
Face Verification — PCA + SVM (elective branch).
Mode A: SVM predicts voter identity, checks against logged-in student_id.
Mode B: Cosine similarity fallback when no trained model is available.
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
THRESHOLD      = 0.55  # cosine similarity threshold (Mode B only)
SVM_THRESHOLD  = 0.50  # minimum SVM confidence to accept (Mode A)


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
    Mode A — SVM identity prediction.
    1. Preprocess the live face into a feature vector.
    2. Run it through the PCA+SVM pipeline to predict who it is.
    3. Verify the predicted student_id matches the logged-in voter.
    Falls back to cosine similarity if the model has no string class labels
    (meaning it was trained before the label encoder was fixed).
    """
    model, le = load_model()

    if model is None or le is None:
        return verify_face_similarity(live_b64, registered_path)

    # Check the label encoder has real student IDs (not integer placeholders)
    if not isinstance(le.classes_[0], str):
        return verify_face_similarity(live_b64, registered_path)

    try:
        live_vector = preprocess_image(live_b64)
    except ValueError as e:
        return {
            "verified":     False,
            "confidence":   0.0,
            "predicted_id": None,
            "method":       "pca_svm",
            "message":      str(e),
        }

    probabilities   = model.predict_proba(live_vector.reshape(1, -1))[0]
    predicted_class = model.predict(live_vector.reshape(1, -1))[0]
    confidence      = float(probabilities.max())
    predicted_id    = le.inverse_transform([predicted_class])[0]

    verified = (predicted_id == student_id) and (confidence >= SVM_THRESHOLD)

    if verified:
        msg = f"SVM confirmed identity. Confidence: {confidence:.0%}."
    elif predicted_id != student_id:
        msg = (
            f"SVM predicted '{predicted_id}' (confidence {confidence:.0%}), "
            f"but expected '{student_id}'. Face does not match."
        )
    else:
        msg = f"Confidence {confidence:.0%} below threshold {SVM_THRESHOLD:.0%}. Please try again."

    return {
        "verified":     verified,
        "confidence":   round(confidence, 4),
        "predicted_id": predicted_id,
        "method":       "pca_svm",
        "message":      msg,
    }


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