# AQUORA — OPERATIONS RUNBOOK

## 1. System Operations Overview [CONFIGURATION VERIFIED]
This runbook provides standard operating procedures for managing, monitoring, and maintaining the AQUORA platform in a production-like deployment environment.

---

## 2. Startup Procedure [DOCUMENTED ONLY]
```bash
# 1. Ensure target environment variables are configured
cp .env.example .env

# 2. Launch container stack in detached mode
docker compose up -d

# 3. Verify container statuses
docker compose ps

# 4. Check readiness status
curl http://localhost:8000/api/v1/health/ready
```

---

## 3. Shutdown Procedure [DOCUMENTED ONLY]
```bash
# 1. Gracefully stop services
docker compose stop

# 2. Tear down containers and networks (preserving volumes)
docker compose down
```

---

## 4. Restart Procedure [DOCUMENTED ONLY]
```bash
# Restart backend service container cleanly
docker compose restart backend
```

---

## 5. Database Migration Procedure [DOCUMENTED ONLY]
```bash
# Apply pending database schema migrations
docker compose exec backend alembic upgrade head

# Check migration head alignment
docker compose exec backend alembic heads
```

---

## 6. Incident Management & Recovery Procedures [DOCUMENTED ONLY]

### Scenario A: PostgreSQL Database Outage
1. Symptom: Readiness check returns `503 Service Unavailable` with `database: error`.
2. Action: Inspect DB container logs: `docker compose logs db`.
3. Restart DB service: `docker compose restart db`.
4. Run readiness check: `curl http://localhost:8000/api/v1/health/ready`.

### Scenario B: Redis Infrastructure Failure
1. Symptom: Readiness check returns `503 Service Unavailable` with `redis: error`.
2. Action: Check Redis container: `docker compose logs redis`.
3. Restart Redis service: `docker compose restart redis`.

---

## 7. Backup & Restore Procedures [DOCUMENTED ONLY]

### Database Dump (PostgreSQL + PostGIS)
```bash
docker compose exec -T db pg_dump -U aquora -d aquora_db > /backups/aquora_db_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore
```bash
cat /backups/aquora_db_backup.sql | docker compose exec -T db psql -U aquora -d aquora_db
```

### Live Recovery Test Status
- `BLOCKED-EXTERNAL / NOT RUN`

---

## 8. Operational Disclaimers [DOCUMENTED ONLY]
- Phase 8 ML model status remains `PROTOTYPE_ONLY`.
- Operational alerts surface decision-support signals and do not guarantee real-world outcomes.
