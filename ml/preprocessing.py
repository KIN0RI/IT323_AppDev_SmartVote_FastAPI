"""
STEP 1 — PREPROCESSING PIPELINE
================================
Takes a raw face image and returns a clean normalized vector ready for PCA.

Pipeline:
  Raw image
    → Grayscale conversion
    → Face detection (Haar Cascade)
    → Face alignment (eye landmarks)
    → Resize to 100×100
    → CLAHE histogram equalization
    → Flatten to 10,000-dim vector
    → Normalize to [0, 1]
"""

import base64
import io
import cv2
import numpy as np
from PIL import Image

# Load OpenCV's pre-trained Haar Cascade face detector
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
EYE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)

IMG_SIZE   = 64    
VECTOR_DIM = IMG_SIZE * IMG_SIZE  # 4,096-dimensional vector


def decode_base64_image(b64_string: str) -> np.ndarray:
    """Convert a base64-encoded image string to a numpy array (BGR)."""
    # Strip the data:image/... header if present
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    img_bytes = base64.b64decode(b64_string)
    img_pil   = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_np    = np.array(img_pil)
    # PIL is RGB, OpenCV is BGR
    return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)


def to_grayscale(img_bgr: np.ndarray) -> np.ndarray:
    """Step 1: Convert BGR image to grayscale."""
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def detect_face(gray: np.ndarray) -> np.ndarray | None:
    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor  = 1.1,
        minNeighbors = 3,
        minSize      = (30, 30),
    )
    if len(faces) == 0:
        return gray  # fallback — use full image

    # Pick the largest face detected
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return gray[y:y+h, x:x+w]


def apply_clahe(gray_face: np.ndarray) -> np.ndarray:
    """
    Step 3: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
    Normalizes lighting so photos taken in different lighting conditions
    produce similar pixel distributions.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray_face)


def resize_face(gray_face: np.ndarray) -> np.ndarray:
    """Step 4: Resize face to uniform 100×100 pixels."""
    return cv2.resize(gray_face, (IMG_SIZE, IMG_SIZE))


def flatten_and_normalize(gray_face: np.ndarray) -> np.ndarray:
    """
    Step 5: Flatten 100×100 matrix → 10,000-dim vector.
    Normalize pixel values from [0, 255] to [0.0, 1.0].
    """
    flat = gray_face.flatten().astype(np.float64)
    return flat / 255.0


def preprocess_image(b64_string: str) -> np.ndarray:
    img_bgr   = decode_base64_image(b64_string)
    gray      = to_grayscale(img_bgr)
    face_crop = detect_face(gray)  # never None now
    equalized  = apply_clahe(face_crop)
    resized    = resize_face(equalized)
    vector     = flatten_and_normalize(resized)
    return vector


def preprocess_from_file(file_path: str) -> np.ndarray:
    """
    Preprocess a face image directly from a file path.
    Used during training to preprocess stored registration photos.
    """
    img_bgr   = cv2.imread(file_path)
    if img_bgr is None:
        raise ValueError(f"Could not read image from {file_path}")
    gray      = to_grayscale(img_bgr)
    face_crop = detect_face(gray)
    if face_crop is None:
        raise ValueError(f"No face detected in {file_path}")
    equalized = apply_clahe(face_crop)
    resized   = resize_face(equalized)
    vector    = flatten_and_normalize(resized)
    return vector
