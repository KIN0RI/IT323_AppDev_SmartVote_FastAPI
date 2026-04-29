# SmartVote FastAPI Backend (Mobile)

FastAPI backend for the **USTP SmartVote** mobile app (Expo/React Native).
Connects to the **same PostgreSQL database** as the Django backend.

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Update database credentials in core/database.py
DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5432/smartvote_db"

# 4. Run the server (port 8001 so it doesn't conflict with Django on 8000)
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## API Docs
Once running, visit:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:**       http://localhost:8001/redoc

## Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Register voter | Public |
| POST | `/api/auth/login-email/` | Login with email | Public |
| GET/PUT | `/api/auth/profile/` | View/edit profile | Student |
| GET | `/api/candidates/` | List candidates | Auth |
| POST | `/api/candidates/` | Add candidate | Admin |
| PUT | `/api/candidates/{id}/` | Update candidate | Admin |
| DELETE | `/api/candidates/{id}/` | Delete candidate | Admin |
| POST | `/api/vote/` | Cast a vote | Student |
| GET | `/api/vote/my/` | My votes | Student |
| GET | `/api/results/` | Election results | Public |
| GET | `/api/dashboard/` | Admin stats | Admin |
| GET | `/api/voter-log/` | Voter log | Admin |
| GET/POST/PUT | `/api/election-settings/` | Election settings | Admin |

## Architecture

```
📱 Mobile App (Expo - port 19000)
        ↓
   FastAPI (port 8001)    ←── this backend
        ↓
   PostgreSQL Database (port 5432)
        ↑
   Django REST (port 8000) ←── web frontend backend
        ↑
🌐 Web App (React - port 5173)
```

Both Django and FastAPI share the same PostgreSQL database!
