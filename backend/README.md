# Aquora Backend API Service

FastAPI-powered modular monolith backend for **AQUORA — Urban Flood Intelligence & Response Platform**.

---

## Technical Stack
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.x (Async)
- **Migrations**: Alembic
- **Database**: PostgreSQL with PostGIS extension
- **Cache**: Redis asyncio client
- **Logging**: Structlog (JSON structured logs)
- **Validation**: Pydantic v2 & `pydantic-settings`
- **Testing**: pytest & pytest-asyncio

---

## Running Backend Locally

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations (requires running PostgreSQL with PostGIS)
alembic upgrade head

# Start Uvicorn development server
uvicorn app.main:app --reload --port 8000
```

---

## Running Tests

```bash
pytest tests/ -v
```
