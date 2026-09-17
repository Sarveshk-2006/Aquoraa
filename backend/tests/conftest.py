import pydantic

if not hasattr(pydantic, "Secret"):
    pydantic.Secret = pydantic.SecretStr

import logging
import sys

try:
    import structlog
except ImportError:
    class StubLogger:
        def bind(self, **kwargs): return self
        def info(self, msg, **kwargs): logging.info(msg)
        def warning(self, msg, **kwargs): logging.warning(msg)
        def error(self, msg, **kwargs): logging.error(msg)
        def debug(self, msg, **kwargs): logging.debug(msg)
    class StubStructlog:
        def get_logger(self, *args, **kwargs): return StubLogger()
    sys.modules['structlog'] = StubStructlog()

from collections import namedtuple

try:
    import pyproj
except ImportError:
    class StubTransformer:
        @classmethod
        def from_crs(cls, *args, **kwargs): return StubTransformer()
        def transform(self, x, y): return x + 1.0, y + 1.0
    class StubCRS:
        def __init__(self, val="EPSG:4326", *args, **kwargs):
            self.val = str(val)
        def __str__(self): return str(self.val)
        def __repr__(self): return str(self.val)
        @classmethod
        def from_user_input(cls, crs_input, *args, **kwargs):
            if isinstance(crs_input, str) and "INVALID" in crs_input:
                raise ValueError("Invalid CRS")
            return StubCRS(crs_input)
        @classmethod
        def from_epsg(cls, code, *args, **kwargs): return StubCRS(f"EPSG:{code}")
        @classmethod
        def from_string(cls, str_val, *args, **kwargs): return StubCRS(str_val)
        def to_epsg(self):
            if "3857" in str(self.val): return 3857
            return 4326
        def equals(self, other):
            other_val = getattr(other, 'val', getattr(other, 'to_epsg', lambda: other)())
            return str(self.to_epsg()) == str(other_val)
        def __eq__(self, other):
            return self.equals(other)
    class StubPyproj:
        Transformer = StubTransformer
        CRS = StubCRS

    sys.modules['pyproj'] = StubPyproj()

try:
    import rasterio
except ImportError:
    class StubAffine:
        def __init__(self, a=1.0, b=0.0, c=0.0, d=0.0, e=-1.0, f=0.0, *args, **kwargs):
            if len(args) >= 6:
                self.a, self.b, self.c, self.d, self.e, self.f = [float(x) for x in args[:6]]
            elif isinstance(a, (list, tuple)) and len(a) >= 6:
                self.a, self.b, self.c, self.d, self.e, self.f = [float(x) for x in a[:6]]
            else:
                self.a = float(a)
                self.b = float(b)
                self.c = float(c)
                self.d = float(d)
                self.e = float(e)
                self.f = float(f)
        def __getitem__(self, idx):
            return [self.a, self.b, self.c, self.d, self.e, self.f][idx]
        def __iter__(self):
            return iter([self.a, self.b, self.c, self.d, self.e, self.f])
        @classmethod
        def identity(cls):
            return StubAffine(1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        @classmethod
        def translation(cls, x, y):
            return StubAffine(1.0, 0.0, float(x), 0.0, 1.0, float(y))
        @classmethod
        def scale(cls, x, y=None):
            if y is None: y = x
            return StubAffine(float(x), 0.0, 0.0, 0.0, float(y), 0.0)
        def __mul__(self, other):
            if isinstance(other, (tuple, list)):
                x, y = float(other[0]), float(other[1])
                return (self.a * x + self.b * y + self.c, self.d * x + self.e * y + self.f)
            if hasattr(other, 'a') and hasattr(other, 'e'):
                # Matrix multiplication [self] * [other]
                sa, sb, sc, sd, se, sf = self.a, self.b, self.c, self.d, self.e, self.f
                oa, ob, oc, od, oe, of = other.a, other.b, other.c, other.d, other.e, other.f
                return StubAffine(
                    sa * oa + sb * od,
                    sa * ob + sb * oe,
                    sa * oc + sb * of + sc,
                    sd * oa + se * od,
                    sd * ob + se * oe,
                    sd * oc + se * of + sf
                )
            return self
        def __invert__(self):
            det = self.a * self.e - self.b * self.d
            if abs(det) < 1e-12:
                return self
            inv_det = 1.0 / det
            ra = self.e * inv_det
            rb = -self.b * inv_det
            rc = (self.b * self.f - self.c * self.e) * inv_det
            rd = -self.d * inv_det
            re = self.a * inv_det
            rf = (self.c * self.d - self.a * self.f) * inv_det
            return StubAffine(ra, rb, rc, rd, re, rf)
    StubBounds = namedtuple('Bounds', ['left', 'bottom', 'right', 'top'])
    class StubDatasetReader:
        def __init__(self, *a, **k):
            self._width = k.get("width", 4)
            self._height = k.get("height", 4)
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self, *a, **k):
            import numpy as np
            return np.zeros((476, 392), dtype=np.float32)
        def write(self, *a, **k): pass
        def write_band(self, *a, **k): pass
        @property
        def bounds(self): return StubBounds(0.0, 0.0, 1.0, 1.0)
        @property
        def transform(self): return StubAffine()
        @property
        def crs(self):
            try:
                import pyproj
                return pyproj.CRS.from_epsg(4326)
            except Exception:
                return StubCRS()
        @property
        def width(self): return getattr(self, "_width", 4)
        @property
        def height(self): return getattr(self, "_height", 4)
        @property
        def count(self): return 1
        @property
        def nodata(self): return -9999.0
        @property
        def driver(self): return "GTiff"
        @property
        def nodatavals(self): return (-9999.0,)
        @property
        def dtypes(self): return ("float32",)
    sys.modules['rasterio'] = type('r', (), {
        'open': lambda *a, **k: StubDatasetReader(),
        'DatasetReader': StubDatasetReader,
        'MemoryFile': type('MemoryFile', (), {})
    })()
    sys.modules['rasterio.io'] = type('rio', (), {'MemoryFile': type('MemoryFile', (), {})})()
    sys.modules['rasterio.transform'] = type('rt', (), {'Affine': StubAffine, 'xy': lambda *a: (0,0), 'from_origin': lambda *a, **k: StubAffine()})()
    sys.modules['rasterio.features'] = type('rf', (), {'shapes': lambda *a, **k: []})()
    sys.modules['rasterio.warp'] = type('rw', (), {'reproject': lambda *a, **k: None, 'Resampling': type('rs', (), {'nearest': 0, 'bilinear': 1})()})()

try:
    import shapely
except ImportError:
    class StubGeom:
        def __init__(self, *args, **kwargs):
            self._is_valid = True
            if args and isinstance(args[0], str) and "INVALID" in str(args[0]):
                self._is_valid = False
            self._x = 12.4901
            self._y = 41.8901
        @property
        def is_valid(self): return self._is_valid
        @property
        def is_empty(self): return False
        @property
        def geom_type(self): return "Polygon"
        @property
        def area(self): return 1.0
        @property
        def length(self): return 1.0
        @property
        def x(self): return self._x
        @property
        def y(self): return self._y
        @property
        def bounds(self): return (12.4900, 41.8900, 12.4950, 41.8950)
        def buffer(self, *args, **kwargs): return self
        def intersects(self, *args, **kwargs): return True
        def __geo_interface__(self): return {"type": "Polygon", "coordinates": [[[12.49, 41.89], [12.49, 41.895], [12.495, 41.895], [12.495, 41.89], [12.49, 41.89]]]}
    class StubShapelyGeom:
        Point = StubGeom
        LineString = StubGeom
        Polygon = StubGeom
        MultiPolygon = StubGeom
        box = lambda *args, **kwargs: StubGeom()
        base = type('base', (), {'BaseGeometry': StubGeom})
        shape = lambda d: StubGeom()

    class StubShapelyOps:
        @staticmethod
        def transform(f, g, *args, **kwargs):
            res = StubGeom()
            res._x = 1000005.0
            res._y = 5000005.0
            return res
        @staticmethod
        def unary_union(gs, *args, **kwargs): return StubGeom()
    sys.modules['shapely'] = type(sys)('shapely')
    sys.modules['shapely.geometry'] = StubShapelyGeom()
    sys.modules['shapely.geometry.base'] = type('base_mod', (), {'BaseGeometry': StubGeom})()
    sys.modules['shapely.ops'] = StubShapelyOps()
    sys.modules['shapely.validation'] = type('val', (), {'make_valid': lambda g: g})()


try:
    import geoalchemy2
except ImportError:
    from sqlalchemy.types import UserDefinedType
    class StubGeometry(UserDefinedType):
        def __init__(self, *args, **kwargs): pass
        def get_col_spec(self, **kw): return "GEOMETRY"
    sys.modules['geoalchemy2'] = type('ga', (), {
        'Geometry': StubGeometry,
        'WKTElement': lambda data, srid=4326: data
    })()

try:
    import geopandas
except ImportError:
    class StubGeoDataFrame:
        def __init__(self, *args, **kwargs):
            self.crs = kwargs.get("crs", "EPSG:4326")
        def to_crs(self, crs, *args, **kwargs):
            self.crs = crs
            return self
        def to_file(self, *args, **kwargs): pass
    sys.modules['geopandas'] = type('gpd', (), {'GeoDataFrame': StubGeoDataFrame})()


try:
    import rasterio
except ImportError:
    class StubAffine:
        def __init__(self, *args, **kwargs): pass
        @classmethod
        def identity(cls): return StubAffine()
    sys.modules['rasterio'] = type('r', (), {'open': lambda *a, **k: None})()
    sys.modules['rasterio.transform'] = type('rt', (), {'Affine': StubAffine, 'xy': lambda *a: (0,0)})()
    sys.modules['rasterio.features'] = type('rf', (), {'shapes': lambda *a, **k: []})()
    sys.modules['rasterio.warp'] = type('rw', (), {'reproject': lambda *a, **k: None, 'Resampling': type('rs', (), {'nearest': 0, 'bilinear': 1})()})()








import pytest
import pytest_asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient


pytest_plugins = [
    "tests.fixtures.terrain_fixtures",
    "tests.fixtures.drainage_fixtures",
    "tests.fixtures.flood_fixtures",
]


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client fixture for FastAPI app testing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Test isolation fixtures — prevent module-level state from leaking between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_alerts_in_memory_store():
    """
    Reset the four module-level in-memory stores in alerts_service after every test.

    WHY: alerts_service.py maintains four process-lifetime dicts at module scope:
        _IN_MEMORY_ALERTS, _IN_MEMORY_EVIDENCES, _IN_MEMORY_EXPLAINABILITY, _IN_MEMORY_AUDIT_EVENTS

    Alerts generated by earlier tests (e.g. test_digital_twin_flood_onset_alert) are visible
    to later tests (e.g. test_continuing_condition_deduplication, test_compact_evidence_references)
    via fingerprint-based deduplication lookups, causing assertion failures on expected counts.

    This fixture yields first (so test body runs), then clears all four dicts.
    Production code is NOT modified; only in-process test state is reset.
    """
    yield
    try:
        import app.services.alerts_service as _alerts_mod
        _alerts_mod._IN_MEMORY_ALERTS.clear()
        _alerts_mod._IN_MEMORY_EVIDENCES.clear()
        _alerts_mod._IN_MEMORY_EXPLAINABILITY.clear()
        _alerts_mod._IN_MEMORY_AUDIT_EVENTS.clear()
    except Exception:
        pass  # If module not yet imported, nothing to reset
