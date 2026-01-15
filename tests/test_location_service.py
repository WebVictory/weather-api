"""Tests for location service"""

import pytest
from unittest.mock import MagicMock, patch
from geopy.location import Location as GeopyLocation

from app.services.location_service import location_service


@pytest.mark.asyncio
async def test_geocode_oslo():
    """Test geocoding Oslo"""
    with patch.object(location_service.geolocator, 'geocode') as mock_geocode:
        # Mock geopy response
        mock_location = MagicMock(spec=GeopyLocation)
        mock_location.latitude = 59.9139
        mock_location.longitude = 10.7522
        mock_location.address = "Oslo, Norway"
        mock_geocode.return_value = mock_location
        
        result = await location_service.geocode("Oslo")
        
        assert result is not None
        lat, lon, name = result
        assert lat == 59.9139
        assert lon == 10.7522
        assert name == "Oslo, Norway"


@pytest.mark.asyncio
async def test_geocode_not_found():
    """Test geocoding location not found"""
    with patch.object(location_service.geolocator, 'geocode') as mock_geocode:
        mock_geocode.return_value = None
        
        result = await location_service.geocode("Atlantis")
        
        assert result is None


@pytest.mark.asyncio
async def test_geocode_cache():
    """Test that geocoding results are cached"""
    # Clear geocoding cache before test
    location_service.cache.clear()
    
    with patch.object(location_service.geolocator, 'geocode') as mock_geocode:
        # Mock geopy response
        mock_location = MagicMock(spec=GeopyLocation)
        mock_location.latitude = 59.9139
        mock_location.longitude = 10.7522
        mock_location.address = "Oslo, Norway"
        mock_geocode.return_value = mock_location
        
        # First call
        result1 = await location_service.geocode("Oslo")
        assert mock_geocode.call_count == 1
        
        # Second call should use cache
        result2 = await location_service.geocode("Oslo")
        assert mock_geocode.call_count == 1  # Not called again
        
        # Results should be identical
        assert result1 == result2


@pytest.mark.asyncio
async def test_geocode_coordinate_truncation():
    """Test that coordinates are truncated to 4 decimals"""
    with patch.object(location_service.geolocator, 'geocode') as mock_geocode:
        # Mock geopy response with high precision
        mock_location = MagicMock(spec=GeopyLocation)
        mock_location.latitude = 59.91398765
        mock_location.longitude = 10.75221234
        mock_location.address = "Oslo, Norway"
        mock_geocode.return_value = mock_location
        
        result = await location_service.geocode("Oslo")
        
        assert result is not None
        lat, lon, name = result
        # Should be truncated to 4 decimals
        assert lat == 59.9139
        assert lon == 10.7522
