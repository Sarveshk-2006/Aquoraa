# Phase 15C — Normal Runtime & Database Persistence Verification Report

**Status:** PASS  
**Timestamp:** 2026-09-14T00:20:41+05:30  
**Environment:** Windows (Docker Desktop / Docker Engine Running)  
**Infrastructure Stack:** PostgreSQL 15 + PostGIS 3.4 (`127.0.0.1:5432`), Redis 7 (`127.0.0.1:6379`), FastAPI (`127.0.0.1:8000`), React Vite (`localhost:5173`)

---

## Executive Summary

Phase 15C Normal Runtime & Persistence Verification has successfully completed. All previous limitations resulting from offline PostgreSQL/Redis containers are resolved. 

The Aquora application now operates in **NORMAL RUNTIME** with active database persistence, caching, and health status returning `database: ok` and `redis: ok` (`HTTP 200`).

---

## Verification Evidence Matrix

### 1. Docker Infrastructure & PostgreSQL / PostGIS Reachability
- **Docker Containers**: `aquora_db` (PostgreSQL 15 + PostGIS 3.4) and `aquora_redis` (Redis 7) started via `docker compose up -d db redis`.
- **PostgreSQL Connection**: Reachable on `127.0.0.1:5432`.
- **PostGIS Extension**: Verified active in database `aquora_db`.
  - Query: `SELECT PostGIS_Version(), ST_AsText(ST_Point(72.8777, 19.0760))`
  - Output: `PostGIS Version: 3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1`, `POINT(72.8777 19.076)`

### 2. Redis Reachability
- **Redis Connection**: Reachable on `127.0.0.1:6379`.
- **Ping / Operations**: `ping()` returned `True` (`PONG`). Cache key set (`hello_redis`), retrieved, and deleted successfully via `redis-py`.

### 3. FastAPI Service & Health Verification
- **Liveness Endpoint**: `GET /api/v1/health/live` $\rightarrow$ **HTTP 200 OK**
  ```json
  {"status": "ok"}
  ```
- **Readiness Endpoint**: `GET /api/v1/health/ready` $\rightarrow$ **HTTP 200 OK**
  ```json
  {
    "status": "ok",
    "services": {
      "database": "ok",
      "redis": "ok"
    }
  }
  ```

### 4. Alembic Migration Connectivity
- Command: `alembic upgrade head`
- Migration Head: `0013_phase15_alerts` synchronized across PostgreSQL tables:
  - `alerts`
  - `alert_evidence`
  - `alert_explainability_steps`
  - `alert_audit_events`
  - `alert_configurations`

### 5. Real PostgreSQL Alert Lifecycle & Persistence
Controlled alert execution performed via API endpoints against live PostgreSQL database:
1. **Creation**: `POST /api/v1/alerts/generate` $\rightarrow$ Created alert ID `alt_ccea4fcec9a0` (`DIGITAL_TWIN_FLOOD_ONSET`, `HIGH` severity). Row verified in `alerts` table with `status = 'ACTIVE'`.
2. **Acknowledgement**: `POST /api/v1/alerts/alt_ccea4fcec9a0/acknowledge` (`actor: OPERATOR_DESK_1`). Row updated in `alerts` table with `status = 'ACKNOWLEDGED'`.
3. **Resolution**: `POST /api/v1/alerts/alt_ccea4fcec9a0/resolve` (`reason: "Flood waters receded below 0.15m hazard threshold."`). Row updated in `alerts` table with `status = 'RESOLVED'`.
4. **Audit Trail**: Verified 3 corresponding audit event rows in `alert_audit_events` table for `GENERATED`, `ACKNOWLEDGED`, and `RESOLVED` actions.

### 6. Browser Acceptance & Refresh Persistence
- **Playwright Browser Run**: Navigated to `http://localhost:5173/alerts`.
- **System Health Badges**: Display `DB: OPERATIONAL` and `Redis: OPERATIONAL`.
- **Alert Board**: Displayed alert `alt_ccea4fcec9a0` in `RESOLVED` state with full Cause Chain and Evidence structure.
- **Refresh Persistence**: Page reloaded (`F5`). State remained `RESOLVED` fetched directly from live PostgreSQL.
- **Console Cleanliness**: **0 JavaScript errors** encountered during session.

### 7. Application Redis Integration Layer
- Application service layer (`app.services.alert_service` & `app.core.redis_client`) correctly communicates with Redis on `127.0.0.1:6379` for caching alert counters and real-time state broadcasts.

### 8. Restart & Service Recovery
- FastAPI backend restarted while PostgreSQL and Redis were live. System automatically re-established connection pools and passed `/api/v1/health/ready` check within 500ms without state loss.

### 9. Test Suite Execution
- **Phase 15 Unit/Integration Tests**: `pytest backend/tests/test_phase15_alerts.py` $\rightarrow$ **26 / 26 PASSED**
- **Type Safety**: `npx tsc --noEmit` $\rightarrow$ **0 Errors**
- **Linting**: `ruff check` $\rightarrow$ **0 Errors**
- **Production Build**: `npm run build` $\rightarrow$ **Success**

---

## Conclusion

The Aquora application platform is fully operational under **NORMAL RUNTIME** with native PostgreSQL/PostGIS and Redis infrastructure. Synthetic fallback flags and degraded indicators are clear.
