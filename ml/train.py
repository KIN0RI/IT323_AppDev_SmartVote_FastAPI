"""
STEP 2 — PCA + SVM MODEL TRAINER
==================================
Trains the Eigenface (PCA) + SVM pipeline on collected voter face images.

How it works:
  1. Load all registered voter face images from media/voter_faces/
  2. Preprocess each image through the pipeline (Step 1)
  3. Fit PCA to find the top 100 Eigenfaces
  4. Project all face vectors into PCA space
  5. Train SVM classifier on the projected vectors
  6. Save the trained model to ml/models/face_model.pkl

Run this script:
  python -m ml.train
"""

import os
import numpy as np
import joblib
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

from ml.preprocessing import preprocess_from_file

# ── Config ────────────────────────────────────────────────────────────────────
FACES_DIR        = "media/voter_faces"
MODEL_PATH       = "ml/models/face_model.pkl"
LABEL_ENC_PATH   = "ml/models/label_encoder.pkl"
N_COMPONENTS     = 100   # number of Eigenfaces (PCA components)
TEST_SIZE        = 0.2   # 80% train, 20% test
RANDOM_STATE     = 42


def load_dataset(faces_dir: str):
    """
    Load all face images from the voter_faces directory.

    Expected folder structure:
      media/voter_faces/
        voter_001/
          photo1.jpg
          photo2.jpg
        voter_002/
          photo1.jpg

    Each subfolder name is the voter's student_id (used as the class label).
    Returns X (feature vectors) and y (class labels).
    """
    X, y = [], []
    voter_dirs = [
        d for d in os.listdir(faces_dir)
        if os.path.isdir(os.path.join(faces_dir, d))
    ]

    if not voter_dirs:
        raise ValueError(
            f"No voter face folders found in {faces_dir}. "
            "Each voter needs a subfolder named by their student_id."
        )

    print(f"Found {len(voter_dirs)} voter(s) in dataset.")

    for voter_id in voter_dirs:
        voter_path = os.path.join(faces_dir, voter_id)
        img_files  = [
            f for f in os.listdir(voter_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        for img_file in img_files:
            img_path = os.path.join(voter_path, img_file)
            try:
                vector = preprocess_from_file(img_path)
                X.append(vector)
                y.append(voter_id)
            except ValueError as e:
                print(f"  Skipping {img_path}: {e}")

    print(f"Total face vectors loaded: {len(X)}")
    return np.array(X), np.array(y)


def train():
    """
    Full training pipeline:
      Load data → PCA → SVM → Evaluate → Save model
    """
    print("\n" + "="*50)
    print("SmartVote Face Verification — Model Training")
    print("="*50)

    # ── Step 1: Load dataset ──────────────────────────────────────────────────
    print("\n[1/5] Loading dataset...")
    X, y = load_dataset(FACES_DIR)

    if len(np.unique(y)) < 2:
        raise ValueError(
            "Need at least 2 different voters to train the model. "
            "Register more voters and add multiple photos per voter."
        )

    # ── Step 2: Encode labels ─────────────────────────────────────────────────
    print("\n[2/5] Encoding class labels...")
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    print(f"  Classes (voters): {list(le.classes_)}")

    # ── Step 3: Train/test split ──────────────────────────────────────────────
    print("\n[3/5] Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size    = TEST_SIZE,
        random_state = RANDOM_STATE,
        stratify     = y_encoded if len(X) >= len(np.unique(y_encoded)) * 2 else None
    )
    print(f"  Training samples : {len(X_train)}")
    print(f"  Test samples     : {len(X_test)}")

    # ── Step 4: Build and train PCA + SVM pipeline ───────────────────────────
    cv_folds = min(5, len(X_train))
    # PCA n_components must fit inside each CV fold's training slice (cv-1)/cv of X_train
    max_for_cv = int(len(X_train) * (cv_folds - 1) / cv_folds) - 1
    n_components = min(N_COMPONENTS, max_for_cv, X_train.shape[1])

    print(f"\n[4/5] Training PCA ({n_components} components) + SVM...")

    pipeline = Pipeline([
        ("pca", PCA(n_components=n_components, whiten=True, random_state=RANDOM_STATE)),
        ("svm", SVC(kernel="rbf", C=1.0, gamma="scale", probability=True, random_state=RANDOM_STATE)),
    ])

    # Use grid search only if we have enough samples
    if len(X_train) >= 10:
        print("  Running grid search for best hyperparameters...")
        param_grid = {
            "svm__C":     [0.1, 1.0, 10.0],
            "svm__gamma": ["scale", "auto"],
        }
        grid_search = GridSearchCV(
            pipeline, param_grid,
            cv=cv_folds,
            n_jobs=-1, verbose=0
        )
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_
        print(f"  Best params: {grid_search.best_params_}")
    else:
        print("  Small dataset — skipping grid search, using default params.")
        pipeline.fit(X_train, y_train)
        best_model = pipeline

    # ── Step 5: Evaluate ──────────────────────────────────────────────────────
    print("\n[5/5] Evaluating model...")
    y_pred    = best_model.predict(X_test)
    accuracy  = accuracy_score(y_test, y_pred)
    print(f"\n  Accuracy: {accuracy * 100:.2f}%")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # ── Save model ────────────────────────────────────────────────────────────
    os.makedirs("ml/models", exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(le,         LABEL_ENC_PATH)
    print(f"\n  Model saved to   : {MODEL_PATH}")
    print(f"  Encoder saved to : {LABEL_ENC_PATH}")
    print("\n" + "="*50)
    print("Training complete! You can now run the FastAPI server.")
    print("="*50 + "\n")

    return best_model, le


if __name__ == "__main__":
    train()
