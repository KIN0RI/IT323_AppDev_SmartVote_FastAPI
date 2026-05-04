import face_recognition
import numpy as np
from PIL import Image
import io
import json

def verify_face(image_bytes: bytes, stored_encoding_json: str) -> dict:
    """Verify face against stored encoding from database."""
    stored_encoding = np.array(json.loads(stored_encoding_json))
    
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(image)
    live_encodings = face_recognition.face_encodings(img_array)
    
    if len(live_encodings) == 0:
        return {"verified": False, "confidence": 0.0, "detail": "No face detected in frame"}
    
    live_encoding = live_encodings[0]
    distance = face_recognition.face_distance([stored_encoding], live_encoding)[0]
    confidence = round((1 - float(distance)) * 100, 2)
    verified = distance < 0.30
    
    return {
        "verified": bool(verified),
        "confidence": float(confidence),
        "detail": "Match" if verified else "Face does not match"
    }

def enroll_face(image_bytes: bytes) -> str:
    """Encode a face from image bytes and return as JSON string."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(image)
    encodings = face_recognition.face_encodings(img_array)
    if len(encodings) == 0:
        raise ValueError("No face detected in image")
    return json.dumps(encodings[0].tolist())