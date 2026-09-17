FROM python:3.11-slim

# Create non-root application execution user
RUN groupadd -g 1000 aquora && useradd -u 1000 -g aquora -m -s /bin/bash aquora

WORKDIR /app
ENV PYTHONPATH=/app

# Install runtime system dependencies for asyncpg, PostGIS / GDAL drivers, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgdal-dev \
    libexpat1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure app ownership for persistent directory writes
RUN chown -R aquora:aquora /app

USER aquora

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "8000"]
