"""Tests for weather service"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.weather_service import WeatherService
from app.services.yrno_client import YrNoClient, YrNoTimeseriesEntry, YrNoTimeseriesData, YrNoInstant, YrNoInstantDetails
from app.api.models import TemperatureUnit


@pytest.fixture
def mock_yrno_client():
    """Create mock yr.no client"""
    client = MagicMock(spec=YrNoClient)
    return client


@pytest.fixture
def weather_service(mock_yrno_client):
    """Create weather service with mocked client"""
    return WeatherService(mock_yrno_client)


@pytest.fixture
def mock_timeseries():
    """Create mock timeseries data"""
    return [
        YrNoTimeseriesEntry(
            time=datetime(2026, 1, 15, 13, 0, 0, tzinfo=timezone.utc),  # 14:00 Belgrade time
            data=YrNoTimeseriesData(
                instant=YrNoInstant(
                    details=YrNoInstantDetails(air_temperature=5.3)
                )
            )
        ),
        YrNoTimeseriesEntry(
            time=datetime(2026, 1, 16, 13, 0, 0, tzinfo=timezone.utc),  # 14:00 Belgrade time
            data=YrNoTimeseriesData(
                instant=YrNoInstant(
                    details=YrNoInstantDetails(air_temperature=6.1)
                )
            )
        ),
    ]


@pytest.mark.asyncio
async def test_get_forecast_days_filter(weather_service, mock_yrno_client, mock_timeseries):
    """Test filtering forecast to specific number of days"""
    mock_yrno_client.fetch_forecast = AsyncMock(return_value=mock_timeseries)

    response = await weather_service.get_forecast(
        lat=44.8125,
        lon=20.4612,
        days=1
    )

    assert len(response.forecasts) == 1
    assert response.days_returned == 1


@pytest.mark.asyncio
async def test_coordinate_truncation(weather_service, mock_yrno_client, mock_timeseries):
    """Test coordinates are truncated to 4 decimals"""
    mock_yrno_client.fetch_forecast = AsyncMock(return_value=mock_timeseries)

    response = await weather_service.get_forecast(
        lat=44.81254321,  # Should be truncated to 44.8125
        lon=20.46123456   # Should be truncated to 20.4612
    )

    assert response.location.latitude == 44.8125
    assert response.location.longitude == 20.4612
