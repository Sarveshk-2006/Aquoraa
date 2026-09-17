from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "NOT_FOUND"})
    message: str = Field(..., json_schema_extra={"example": "The requested resource was not found."})
    request_id: str = Field(..., json_schema_extra={"example": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"})

class ApiErrorResponse(BaseModel):
    error: ErrorDetail
