# PinkRoute AI backend

FastAPI + PostgreSQL + XGBoost API for `frontend/index.html`.

## 1. Start PostgreSQL

```bash
cd backend
docker compose up -d
```

Create the database if Postgres is already installed locally:

```sql
CREATE DATABASE pinkroute;
```

## 2. Install and train

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python train_model.py
python seed.py
```

The API also trains models and seeds data automatically on first start if they are missing.

## 3. Run the API

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs

## Frontend endpoints used

| UI | Method | Path |
| --- | --- | --- |
| Dashboard | GET | `/api/dashboard/` |
| Bus detail | GET | `/api/buses/{bus_number}` |
| Live tracking | GET | `/api/routes/{route}/tracking` |
| ETA | GET | `/api/routes/{route}/eta?stop_name=` |
| Compare routes | GET | `/api/routes/compare?from_stop=&to_stop=` |
| Crowd forecast | GET | `/api/crowd/{route}` |
| Alerts | GET | `/api/alerts/` |
| Chat | POST | `/api/chat/` |
| Smart departure | GET | `/api/departure/?required_arrival=09:00` |
