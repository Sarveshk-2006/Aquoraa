import inspect

from app.providers import (
    BaseForecastProvider,
    BaseLandCoverProvider,
    BaseRainfallProvider,
    BaseRoadNetworkProvider,
    BaseRoutingProvider,
    BaseSatelliteProvider,
    BaseTerrainProvider,
)


def test_provider_interfaces_importable():
    """Verify all external data provider abstract interfaces are importable and defined."""
    providers = [
        BaseRainfallProvider,
        BaseForecastProvider,
        BaseTerrainProvider,
        BaseLandCoverProvider,
        BaseRoadNetworkProvider,
        BaseSatelliteProvider,
        BaseRoutingProvider,
    ]
    for provider in providers:
        assert inspect.isclass(provider)
        assert inspect.isabstract(provider)
