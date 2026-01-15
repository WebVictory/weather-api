"""Tests for Pydantic models"""

import pytest
from datetime import date, time, datetime
from pydantic import ValidationError

from app.api.models import (
    Location,
    TemperatureUnit,
    TemperatureReading,
    ForecastRequest,
    ForecastResponse,
    HealthStatus,
    ErrorResponse
)


class TestLocation:
    """Tests for Location model"""
    
    def test_valid_location(self):
        """Test valid location creation"""
        loc = Location(latitude=44.8125, longitude=20.4612, name="Belgrade")
        assert loc.latitude == 44.8125
        assert loc.longitude == 20.4612
        assert loc.name == "Belgrade"
    
    def test_coordinate_truncation(self):
        """Test coordinates are truncated to 4 decimals"""
        loc = Location(latitude=44.81254321, longitude=20.46123456)
        assert loc.latitude == 44.8125
        assert loc.longitude == 20.4612
    
    def test_invalid_latitude(self):
        """Test invalid latitude raises error"""
        with pytest.raises(ValidationError):
            Location(latitude=100.0, longitude=20.0)
        
        with pytest.raises(ValidationError):
            Location(latitude=-100.0, longitude=20.0)
    
    def test_invalid_longitude(self):
        """Test invalid longitude raises error"""
        with pytest.raises(ValidationError):
            Location(latitude=40.0, longitude=200.0)
        
        with pytest.raises(ValidationError):
            Location(latitude=40.0, longitude=-200.0)


class TestTemperatureUnit:
    """Tests for TemperatureUnit enum"""
    
    def test_celsius_conversion(self):
        """Test Celsius to Celsius conversion"""
        unit = TemperatureUnit.CELSIUS
        assert unit.convert_from_celsius(0.0) == 0.0
        assert unit.convert_from_celsius(100.0) == 100.0
    
    def test_fahrenheit_conversion(self):
        """Test Celsius to Fahrenheit conversion"""
        unit = TemperatureUnit.FAHRENHEIT
        assert unit.convert_from_celsius(0.0) == 32.0
        assert unit.convert_from_celsius(100.0) == 212.0
        assert abs(unit.convert_from_celsius(20.0) - 68.0) < 0.01


class TestTemperatureReading:
    """Tests for TemperatureReading model"""
    
    def test_valid_reading(self):
        """Test valid temperature reading creation"""
        reading = TemperatureReading(
            date=date(2026, 1, 15),
            temperature=5.3,
            unit=TemperatureUnit.CELSIUS,
            time=time(14, 0, 0),
            source_time=datetime(2026, 1, 15, 13, 0, 0)
        )
        assert reading.temperature == 5.3
        assert reading.unit == TemperatureUnit.CELSIUS


class TestForecastRequest:
    """Tests for ForecastRequest model"""
    
    def test_default_to_belgrade(self):
        """Test defaults to Belgrade when no location provided"""
        req = ForecastRequest()
        assert req.latitude == 44.8125
        assert req.longitude == 20.4612
    
    def test_with_coordinates(self):
        """Test with explicit coordinates"""
        req = ForecastRequest(latitude=59.9139, longitude=10.7522)
        assert req.latitude == 59.9139
        assert req.longitude == 10.7522
    
    def test_with_location_name(self):
        """Test with location name"""
        req = ForecastRequest(location_name="Oslo")
        assert req.location_name == "Oslo"
    
    def test_default_unit(self):
        """Test default unit is Celsius"""
        req = ForecastRequest()
        assert req.unit == TemperatureUnit.CELSIUS
    
    def test_days_validation(self):
        """Test days parameter validation"""
        # Valid days
        req = ForecastRequest(days=5)
        assert req.days == 5
        
        # Invalid days (too low)
        with pytest.raises(ValidationError):
            ForecastRequest(days=0)
        
        # Invalid days (too high)
        with pytest.raises(ValidationError):
            ForecastRequest(days=11)


class TestForecastResponse:
    """Tests for ForecastResponse model"""
    
    def test_forecasts_sorted(self):
        """Test forecasts are automatically sorted by date"""
        loc = Location(latitude=44.8125, longitude=20.4612)
        readings = [
            TemperatureReading(
                date=date(2026, 1, 17),
                temperature=6.0,
                time=time(14, 0),
                source_time=datetime(2026, 1, 17, 13, 0)
            ),
            TemperatureReading(
                date=date(2026, 1, 15),
                temperature=5.0,
                time=time(14, 0),
                source_time=datetime(2026, 1, 15, 13, 0)
            ),
        ]
        
        response = ForecastResponse(
            location=loc,
            forecasts=readings,
            days_returned=2
        )
        
        assert response.forecasts[0].date == date(2026, 1, 15)
        assert response.forecasts[1].date == date(2026, 1, 17)
    
    def test_days_returned_auto_calculated(self):
        """Test days_returned is automatically calculated"""
        loc = Location(latitude=44.8125, longitude=20.4612)
        readings = [
            TemperatureReading(
                date=date(2026, 1, 15),
                temperature=5.0,
                time=time(14, 0),
                source_time=datetime(2026, 1, 15, 13, 0)
            ),
        ]
        
        response = ForecastResponse(
            location=loc,
            forecasts=readings,
            days_returned=999  # Should be overridden
        )
        
        assert response.days_returned == 1


class TestHealthStatus:
    """Tests for HealthStatus model"""
    
    def test_valid_health_status(self):
        """Test valid health status creation"""
        status = HealthStatus(
            status="healthy",
            version="1.0.0",
            uptime_seconds=100.5,
            yrno_available=True,
            cache_size=10,
            cache_hit_rate=85.5
        )
        assert status.status == "healthy"
        assert status.yrno_available is True


class TestErrorResponse:
    """Tests for ErrorResponse model"""
    
    def test_simple_error(self):
        """Test simple error without details"""
        err = ErrorResponse(
            error="NotFound",
            message="Resource not found"
        )
        assert err.error == "NotFound"
        assert err.message == "Resource not found"
        assert err.details is None
    
    def test_error_with_details(self):
        """Test error with details"""
        err = ErrorResponse(
            error="ValidationError",
            message="Invalid input",
            details={"field": "latitude", "value": 100}
        )
        assert err.details["field"] == "latitude"
