# USTP SmartVote — Backend API

FastAPI backend for the USTP SmartVote student election system. Handles authentication, face recognition, voting, and election management.

## Deployment

| Platform | URL |
|----------|-----|
| API (Render) | https://it323-appdev-smartvote-fastapi.onrender.com |
| API Docs | https://it323-appdev-smartvote-fastapi.onrender.com/docs |

## Tech Stack

| | |
|-|-|
| Framework | FastAPI (Python) |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Auth | JWT (python-jose) |
| Face Recognition | OpenCV (Haar Cascade), PCA + SVM / Cosine Similarity |
| Deployment | Render |

## Face Verification Modes

- PCA + Cosine Similarity fallback (before training)
- CLAHE histogram equalization for lighting normalization

## Local Development

**Prerequisites:** Python 3.10+, PostgreSQL

1. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/smartvote_db
SECRET_KEY=your-secret-key
```

4. Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

5. Open API docs at `http://localhost:8001/docs`

An admin account is created automatically on first startup:
- **Email:** admin@ustp.edu.ph
- **Password:** admin1234

## Deployment (Render)

1. Connect this repository to a Render Web Service
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `DATABASE_URL` — Render PostgreSQL external URL
   - `SECRET_KEY` — any random string

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new student |
| POST | `/api/auth/login-email/` | Login with email + password |
| GET | `/api/auth/profile/` | Get current user profile |
| POST | `/api/face/register-face/` | Register face photo |
| POST | `/api/face/verify/` | Verify face identity |
| POST | `/api/face/train/` | Train PCA+SVM model (admin) |
| GET | `/api/candidates/` | List all candidates |
| POST | `/api/vote/` | Cast a vote |
| GET | `/api/results/` | View election results |
| GET | `/api/dashboard/` | Admin dashboard stats |
| GET | `/api/election-settings/` | Get election settings |
| GET | `/api/voter-log/` | View voter log (admin) |

## Group Members

- Nepthalie Brynt R. Asinero
- Dan Ivan E. Labin
- Christian Paul L. Bahian
- Ronald E. Yu

## Course

IT323 - Application Development and Emerging Technologies