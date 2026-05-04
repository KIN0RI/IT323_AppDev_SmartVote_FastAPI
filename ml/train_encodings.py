import face_recognition
import pickle
from pathlib import Path

FACES_DIR = "faces/"
OUTPUT_PKL = "ml/face_encodings.pkl"

def build_encodings():
    known_encodings = []
    known_ids = []

    image_files = list(Path(FACES_DIR).glob("*.jpg")) + list(Path(FACES_DIR).glob("*.png"))

    if len(image_files) == 0:
        print("ERROR: No images found in faces/ folder.")
        return

    for img_path in image_files:
        student_id = img_path.stem
        print(f"Processing: {student_id}...")
        image = face_recognition.load_image_file(str(img_path))
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            print(f"  WARNING: No face detected in {img_path.name}, skipping.")
            continue

        known_encodings.append(encodings[0])
        known_ids.append(student_id)
        print(f"  OK: {student_id} encoded.")

    if len(known_ids) == 0:
        print("ERROR: No faces were encoded. Check your photos.")
        return

    data = {"encodings": known_encodings, "ids": known_ids}
    with open(OUTPUT_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"Done! {len(known_ids)} faces saved to {OUTPUT_PKL}")

if __name__ == "__main__":
    build_encodings()
