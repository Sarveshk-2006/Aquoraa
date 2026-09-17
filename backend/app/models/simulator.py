"""
SQLAlchemy PostGIS Models for Phase 14 Aquora Simulator.

Tracks scenario definitions, run execution state, map artifacts,
baseline vs scenario metric comparisons, and solver diagnostics.
"""

import datetime
from typing import Optional, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SimulatorScenario(Base):
    """
    Definition of a what-if hydro-simulation scenario.
    """
    __tablename__ = "simulator_scenarios"

    scenario_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    baseline_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False, default="RAINFALL_MULTIPLIER")

    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    assumptions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default="[]")

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    runs: Mapped[list["SimulatorRun"]] = relationship(
        "SimulatorRun",
        back_populates="scenario",
        cascade="all, delete-orphan"
    )


class SimulatorRun(Base):
    """
    Execution run of a simulator scenario against Phase 6 flood engine.
    """
    __tablename__ = "simulator_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("simulator_scenarios.scenario_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    baseline_run_id: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RUNNING")

    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    engine_version: Mapped[str] = mapped_column(String(64), nullable=False, default="Phase6_FloodEngine_v1")
    config_version: Mapped[str] = mapped_column(String(64), nullable=False, default="Phase14_SimulatorConfig_v1")

    warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    scenario: Mapped["SimulatorScenario"] = relationship("SimulatorScenario", back_populates="runs")
    artifacts: Mapped[list["SimulatorArtifact"]] = relationship("SimulatorArtifact", back_populates="run", cascade="all, delete-orphan")
    comparisons: Mapped[list["SimulatorComparison"]] = relationship("SimulatorComparison", back_populates="run", cascade="all, delete-orphan")
    diagnostics: Mapped[list["SimulatorDiagnostic"]] = relationship("SimulatorDiagnostic", back_populates="run", cascade="all, delete-orphan")


class SimulatorArtifact(Base):
    """
    File-backed raster output references generated during scenario runs.
    """
    __tablename__ = "simulator_artifacts"

    artifact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("simulator_runs.run_id", ondelete="CASCADE"),
        nullable=False
    )

    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, default="RASTER_SLICE")
    storage_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    crs: Mapped[str] = mapped_column(String(32), nullable=False, default="EPSG:32643")
    transform: Mapped[list[float]] = mapped_column(JSONB, nullable=False, server_default="[]")
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nodata: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    run: Mapped["SimulatorRun"] = relationship("SimulatorRun", back_populates="artifacts")


class SimulatorComparison(Base):
    """
    Baseline vs scenario comparison metrics for a timeline slice.
    """
    __tablename__ = "simulator_comparisons"

    comparison_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("simulator_runs.run_id", ondelete="CASCADE"),
        nullable=False
    )

    slice_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    baseline_metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    scenario_metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    deltas: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="NO_SIGNIFICANT_CHANGE")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    run: Mapped["SimulatorRun"] = relationship("SimulatorRun", back_populates="comparisons")


class SimulatorDiagnostic(Base):
    """
    Hydro-solver diagnostic metrics (e.g. mass balance, numerical stability).
    """
    __tablename__ = "simulator_diagnostics"

    diagnostic_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("simulator_runs.run_id", ondelete="CASCADE"),
        nullable=False
    )

    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="VALID")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    run: Mapped["SimulatorRun"] = relationship("SimulatorRun", back_populates="diagnostics")
