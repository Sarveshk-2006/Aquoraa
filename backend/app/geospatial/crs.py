import structlog
from app.core.config import settings
from pyproj import CRS, Transformer
from shapely.geometry import base
from shapely.ops import transform

logger = structlog.get_logger("aquora.geospatial.crs")

class CRSManager:
    """
    Centralized Spatial Reference System (CRS) Manager.
    
    Enforces architectural separation:
    - Canonical CRS (EPSG:4326): Geographic coordinates for interchange and storage.
    - Display CRS (EPSG:3857): Web Mercator for web UI rendering.
    - Analysis CRS (Configurable, default EPSG:32633): Metric projected CRS for planar spatial analysis.
    """
    
    @staticmethod
    def parse_crs(crs_input: str | int | CRS) -> CRS:
        """Parse CRS input into a validated PyProj CRS object."""
        if isinstance(crs_input, CRS):
            return crs_input
        if isinstance(crs_input, int):
            return CRS.from_epsg(crs_input)
        if isinstance(crs_input, str):
            return CRS.from_user_input(crs_input)
        raise ValueError(f"Invalid CRS input type: {type(crs_input)}")

    @classmethod
    def validate_crs(cls, crs_input: str | int | CRS) -> bool:
        """Verify if a given CRS specification is valid."""
        try:
            cls.parse_crs(crs_input)
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning("CRS validation failed", error=str(e), crs_input=str(crs_input))
            return False

    @classmethod
    def are_crs_equal(cls, crs_a: str | int | CRS, crs_b: str | int | CRS) -> bool:
        """Check equality between two spatial reference systems."""
        parsed_a = cls.parse_crs(crs_a)
        parsed_b = cls.parse_crs(crs_b)
        return parsed_a == parsed_b

    @classmethod
    def get_transformer(cls, source_crs: str | int | CRS, target_crs: str | int | CRS) -> Transformer:
        """Create a PyProj coordinate transformer using always_xy=True."""
        parsed_source = cls.parse_crs(source_crs)
        parsed_target = cls.parse_crs(target_crs)
        return Transformer.from_crs(parsed_source, parsed_target, always_xy=True)

    @classmethod
    def transform_geometry(
        cls,
        geometry: base.BaseGeometry,
        source_crs: str | int | CRS,
        target_crs: str | int | CRS
    ) -> base.BaseGeometry:
        """
        Transform a Shapely geometry from source_crs to target_crs.
        If source_crs equals target_crs, returns geometry unchanged.
        """
        if cls.are_crs_equal(source_crs, target_crs):
            return geometry
        
        transformer = cls.get_transformer(source_crs, target_crs)
        return transform(transformer.transform, geometry)

    @classmethod
    def to_canonical(
        cls,
        geometry: base.BaseGeometry,
        source_crs: str | int | CRS
    ) -> base.BaseGeometry:
        """Transform geometry from source_crs to Canonical CRS (EPSG:4326)."""
        return cls.transform_geometry(geometry, source_crs, settings.GEOSPATIAL_CANONICAL_CRS)

    @classmethod
    def to_analysis(
        cls,
        geometry: base.BaseGeometry,
        source_crs: str | int | CRS = None
    ) -> base.BaseGeometry:
        """Transform geometry from source_crs (or Canonical) to active Analysis CRS."""
        source = source_crs if source_crs else settings.GEOSPATIAL_CANONICAL_CRS
        return cls.transform_geometry(geometry, source, settings.GEOSPATIAL_ANALYSIS_CRS)

    @classmethod
    def to_display(
        cls,
        geometry: base.BaseGeometry,
        source_crs: str | int | CRS = None
    ) -> base.BaseGeometry:
        """Transform geometry from source_crs (or Canonical) to Display CRS (EPSG:3857)."""
        source = source_crs if source_crs else settings.GEOSPATIAL_CANONICAL_CRS
        return cls.transform_geometry(geometry, source, settings.GEOSPATIAL_DISPLAY_CRS)
