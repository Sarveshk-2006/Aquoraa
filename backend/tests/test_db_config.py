from app.db.base import Base
from app.models.audit import AuditEvent
from app.models.model_run import ModelRun


def test_database_models_metadata():
    """Verify Phase 0 audit and model_runs table metadata exist in SQLAlchemy Base."""
    assert AuditEvent.__tablename__ == "audit_events"
    assert ModelRun.__tablename__ == "model_runs"
    table_names = list(Base.metadata.tables.keys())
    assert "audit_events" in table_names
    assert "model_runs" in table_names

def test_audit_event_columns():
    """Verify audit_events table column names."""
    table = Base.metadata.tables[AuditEvent.__tablename__]
    column_names = [col.name for col in table.columns]
    expected = [
        "id", "timestamp", "actor", "action", "entity_type", "entity_id",
        "old_value", "new_value", "model_version", "data_version", "reason", "metadata"
    ]
    for col in expected:
        assert col in column_names

def test_model_run_columns():
    """Verify model_runs table column names."""
    table = Base.metadata.tables[ModelRun.__tablename__]
    column_names = [col.name for col in table.columns]
    expected = [
        "id", "model_version", "dataset_version", "feature_version",
        "input_timestamp", "forecast_horizon", "created_at", "status", "metrics_reference"
    ]
    for col in expected:
        assert col in column_names
