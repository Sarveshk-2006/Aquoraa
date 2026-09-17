
import structlog
from shapely.geometry import MultiPolygon, Polygon, base
from shapely.validation import make_valid

logger = structlog.get_logger("aquora.geospatial.validation")

class GeometryValidationError(Exception):
    """Exception raised when geometry fails validation criteria."""

def validate_geometry(
    geometry: base.BaseGeometry | None,
    expected_type: str | None = None,
    allow_empty: bool = False
) -> bool:
    """
    Validates presence, non-empty state, validity, and optionally expected geometry type.
    Raises GeometryValidationError if validation fails.
    """
    if geometry is None:
        raise GeometryValidationError("Geometry is None")
    
    if not allow_empty and geometry.is_empty:
        raise GeometryValidationError("Geometry is empty")
        
    if not geometry.is_valid:
        raise GeometryValidationError(f"Invalid geometry structure: {geometry.geom_type}")

    if expected_type and geometry.geom_type.lower() != expected_type.lower():
        raise GeometryValidationError(
            f"Geometry type mismatch. Expected: '{expected_type}', got: '{geometry.geom_type}'"
        )

    return True

def ensure_valid_polygon(polygon: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    """
    Validates a polygon geometry. If invalid, applies shapely.validation.make_valid
    and logs an explicit audit warning when a repair is performed.
    """
    if polygon is None or polygon.is_empty:
        raise GeometryValidationError("Cannot validate empty or None polygon")

    if polygon.is_valid:
        return polygon

    logger.warning(
        "Invalid polygon detected. Applying explicit geometry repair via make_valid",
        original_type=polygon.geom_type
    )
    
    repaired = make_valid(polygon)
    
    if repaired.is_empty or not repaired.is_valid:
        raise GeometryValidationError("Failed to repair invalid polygon geometry")

    return repaired

def check_srid(srid: int, expected_srid: int) -> bool:
    """Check if provided SRID matches expected integer SRID code."""
    if srid != expected_srid:
        raise GeometryValidationError(f"SRID mismatch. Expected: {expected_srid}, got: {srid}")
    return True

def validate_bbox(bbox: tuple[float, float, float, float]) -> bool:
    """
    Validates bounding box coordinates tuple (min_x, min_y, max_x, max_y).
    """
    if len(bbox) != 4:
        raise GeometryValidationError("Bounding box must be a tuple of 4 float values: (min_x, min_y, max_x, max_y)")
        
    min_x, min_y, max_x, max_y = bbox
    
    if min_x >= max_x:
        raise GeometryValidationError(f"Invalid bounding box width: min_x ({min_x}) >= max_x ({max_x})")
        
    if min_y >= max_y:
        raise GeometryValidationError(f"Invalid bounding box height: min_y ({min_y}) >= max_y ({max_y})")

    return True
