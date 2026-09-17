from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    status: str = Field("ok", json_schema_extra={"example": "ok"})

class ServicesHealth(BaseModel):
    database: str = Field(..., json_schema_extra={"example": "ok"})
    redis: str = Field(..., json_schema_extra={"example": "ok"})
    schema_migration: str = Field("ok", json_schema_extra={"example": "ok"})
    terrain_assets: str = Field("ok", json_schema_extra={"example": "ok"})

class ReadinessResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    environment: str = Field(..., json_schema_extra={"example": "production"})
    services: ServicesHealth

# Backward compatibility alias
HealthResponse = ReadinessResponse
