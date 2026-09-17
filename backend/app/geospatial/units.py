"""
Geospatial & Rainfall Unit Conversion and Quality Semantics Utilities.

Provides strict mathematical unit conversions (accumulation vs. intensity rate)
and quality sentinel handling (distinguishing NODATA from measured 0.0 zero rainfall).
"""

import structlog

logger = structlog.get_logger("aquora.geospatial.units")

# Constants
MM_PER_INCH = 25.4


def convert_accumulation_to_intensity(accumulation_mm: float, interval_minutes: float) -> float:
    """
    Convert rainfall accumulation over an interval (mm) to hourly intensity rate (mm/h).
    
    Formula: rate_mm_h = (accumulation_mm / interval_minutes) * 60.0
    """
    if interval_minutes <= 0:
        raise ValueError(f"Interval minutes must be strictly positive, got: {interval_minutes}")
    if accumulation_mm < 0:
        raise ValueError(f"Negative rainfall accumulation is invalid: {accumulation_mm}")
        
    return (accumulation_mm / interval_minutes) * 60.0


def convert_intensity_to_accumulation(intensity_mm_h: float, interval_minutes: float) -> float:
    """
    Convert hourly rainfall intensity rate (mm/h) to accumulation (mm) over an interval.
    
    Formula: accumulation_mm = (intensity_mm_h / 60.0) * interval_minutes
    """
    if interval_minutes <= 0:
        raise ValueError(f"Interval minutes must be strictly positive, got: {interval_minutes}")
    if intensity_mm_h < 0:
        raise ValueError(f"Negative rainfall intensity is invalid: {intensity_mm_h}")

    return (intensity_mm_h / 60.0) * interval_minutes


def convert_inches_to_mm(inches: float) -> float:
    """Convert inches to millimeters."""
    if inches < 0:
        raise ValueError(f"Negative rainfall value in inches is invalid: {inches}")
    return inches * MM_PER_INCH


def convert_mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    if mm < 0:
        raise ValueError(f"Negative rainfall value in mm is invalid: {mm}")
    return mm / MM_PER_INCH


def is_nodata_value(val: float | None, nodata_sentinel: float | None = -9999.0) -> bool:
    """
    Check if a numeric value matches the NODATA sentinel.
    
    CRITICAL DISTINCTION:
    - True: Value is missing/nodata.
    - False: Value is a valid measurement (including 0.0 zero rainfall).
    """
    if val is None:
        return True
    return nodata_sentinel is not None and abs(val - nodata_sentinel) < 1e-4
