# Aquora — Reproducible Hackathon Deployment & Setup Guide

**Version:** 0.6.0-phase17  
**Runtime Requirements:** Docker Desktop / Docker Engine (Linux containers), Python 3.11/3.12, Node.js 18+  
**Target Environment:** Local / Bare-Metal / Cloud VM Container Host

---

## 1. Executive Overview

Aquora is an integrated urban flood intelligence and emergency decision-support platform designed for the Mumbai Mithi River catchment corridor (Kurla / Saki Naka / Kalina / Sion).

### Infrastructure Architecture
$$\text{React Vite Frontend (Port 5173)} \leftrightarrow \text{FastAPI Monolith (Port 8000)} \leftrightarrow \begin{cases} \text{PostgreSQL 15 + PostGIS 3.4 (Port 5432)} \\ \text{Redis 7 Cache \& Pub/Sub (Port 6379)} \end{cases}$$

---

## 2. Prerequisites & Tools

Ensure the following tools are installed on the host machine:
- **Docker Desktop** (or Docker Engine 24.0+) with `docker compose` CLI plugin.
- **Git** for repository retrieval.
- (Optional for non-containerized local dev): Python 3.12, Node.js 20, npm 10.

---

## 3. Quick Start (Standard Docker Compose Setup)

The simplest and most reliable method to start the complete Aquora stack is using **Docker Compose**:

### Step 1: Clone Repository & Create Environment File
```bash
git clone https://github.com/aquora-platform/nextstep-hacks.git
cd nextstep-hacks
cp .env.example .env
```

### Step 2: Validate Docker Compose Configuration
```bash
docker compose config
```

### Step 3: Launch Services Stack
```bash
docker compose up -d db redis backend frontend
```

### Step 4: Verify Infrastructure Health & Readiness
```bash
# Check container status
docker ps

# Verify Liveness
curl http://localhost:8000/api/v1/health/live

# Verify Readiness (PostgreSQL + Redis connection pool ready)
curl http://localhost:8000/api/v1/health/ready
```
Expected Readiness Output:
```json
{
  "status": "ok",
  "services": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### Step 5: Access the Web Application
Open your web browser and navigate to:
```
http://localhost:5173/
```

---

## 4. Manual / Development Environment Setup

If running backend and frontend directly on the host machine for local development:

### Step 1: Start Database & Redis via Docker
```bash
docker compose up -d db redis
```

### Step 2: Set Up Backend Virtual Environment
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Run Database Migrations
```bash
# Set DATABASE_URL if running locally outside container
$env:DATABASE_URL="postgresql+asyncpg://aquora:aquora_password@127.0.0.1:5432/aquora_db"
alembic upgrade head
```

### Step 4: Launch FastAPI Backend Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Set Up & Launch Frontend Dev Server
```bash
cd ../frontend
npm install
npm run dev
```

---

## 5. Environment Variables & Security Reference

| Parameter | Default Value | Purpose / Notes |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://aquora:aquora_password@db:5432/aquora_db` | Async PostgreSQL/PostGIS connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis caching & pub/sub URL |
| `ENVIRONMENT` | `production-like` | Runtime mode (`development`, `production-like`) |
| `API_BASE_URL` | `http://localhost:8000` | Base URL for FastAPI backend endpoints |
| `CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | Allowed CORS origins for frontend requests |
| `LOG_LEVEL` | `INFO` | Logging output level |
| `GEOSPATIAL_ANALYSIS_CRS` | `EPSG:32643` | Projected metric CRS (UTM 43N for Mumbai Mithi) |

> [!IMPORTANT]
> NASA Earthdata credentials (`NASA_EARTHDATA_USERNAME`, `NASA_EARTHDATA_PASSWORD`) MUST remain backend-only environment variables. Never expose them to frontend code or client bundles.

---

## 6. Restart & Recovery Procedures

### Graceful Restart
```bash
docker compose restart backend frontend
```

### Infrastructure Recovery (PostgreSQL / Redis Disruption)
If PostgreSQL or Redis is restarted during runtime, FastAPI automatically recovers connection pools within 500ms without requiring a backend restart.

### Clean Data Teardown & Reconstruction (Optional)
```bash
docker compose down -v
docker compose up -d db redis
# Run migrations to rebuild fresh schema
```

---

## 7. Explicit Preserved Scientific Limitations

1. **Underground Municipal Drainage Telemetry**: Physical sensor telemetry for underground pipe networks is not available in real-time; drainage is represented using available surface elevation proxy and slope modeling rather than real-time underground pipe telemetry.
2. **Kaggle XGBoost Prototype ML**: XGBoost model (`backend/data/models/aquora_xgboost_prototype.joblib`) is strictly tagged as `PROTOTYPE_ONLY` and calibrated on historical Kaggle benchmark events; the physical flood engine remains the primary authority.
