"""Tests for timezone service"""

import pytest
from datetime import datetime
import pytz

from app.services.timezone_service import timezone_service


def test_get_timezone_belgrade():
    """Test timezone detection for Belgrade"""
    tz = timezone_service.get_timezone(44.8125, 20.4612)

    assert tz.zone == "Europe/Belgrade"


def test_get_timezone_oslo():
    """Test timezone detection for Oslo"""
    tz = timezone_service.get_timezone(59.9139, 10.7522)

    assert tz.zone == "Europe/Oslo"


def test_get_timezone_new_york():
    """Test timezone detection for New York"""
    tz = timezone_service.get_timezone(40.7128, -74.0060)

    assert tz.zone == "America/New_York"


def test_get_timezone_override():
    """Test timezone override"""
    # Request Belgrade coordinates with Oslo timezone
    tz = timezone_service.get_timezone(44.8125, 20.4612, tz_override="Europe/Oslo")

    assert tz.zone == "Europe/Oslo"


def test_get_timezone_invalid_override():
    """Test invalid timezone override falls back to auto-detection"""
    tz = timezone_service.get_timezone(44.8125, 20.4612, tz_override="Invalid/Timezone")

    # Should fall back to auto-detected timezone
    assert tz.zone == "Europe/Belgrade"


def test_get_timezone_ocean():
    """Test timezone for ocean coordinates (should fall back to UTC or similar)"""
    # Middle of Atlantic Ocean
    tz = timezone_service.get_timezone(0.0, -30.0)

    # timezonefinder may return various UTC-based zones for ocean
    assert "UTC" in tz.zone or "GMT" in tz.zone


def test_to_local_time_belgrade():
    """Test UTC to local time conversion for Belgrade"""
    utc_time = datetime(2026, 1, 15, 13, 0, 0, tzinfo=pytz.UTC)

    local_time = timezone_service.to_local_time(utc_time, 44.8125, 20.4612)

    # Belgrade is UTC+1 in winter
    assert local_time.hour == 14
    assert local_time.tzinfo.zone == "Europe/Belgrade"


def test_to_local_time_oslo():
    """Test UTC to local time conversion for Oslo"""
    utc_time = datetime(2026, 1, 15, 13, 0, 0, tzinfo=pytz.UTC)

    local_time = timezone_service.to_local_time(utc_time, 59.9139, 10.7522)

    # Oslo is UTC+1 in winter
    assert local_time.hour == 14
    assert local_time.tzinfo.zone == "Europe/Oslo"


def test_validate_timezone_valid():
    """Test timezone validation for valid timezone"""
    assert timezone_service.validate_timezone("Europe/Oslo") is True
    assert timezone_service.validate_timezone("America/New_York") is True
    assert timezone_service.validate_timezone("UTC") is True


def test_validate_timezone_invalid():
    """Test timezone validation for invalid timezone"""
    assert timezone_service.validate_timezone("Invalid/Timezone") is False
    assert timezone_service.validate_timezone("Not_A_Timezone") is False
