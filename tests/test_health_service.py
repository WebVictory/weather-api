"""Tests for health service"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.health_service import HealthService
from app.services.yrno_client import YrNoClient


@pytest.fixture
def mock_yrno_client():
    """Create mock yr.no client"""
    client = MagicMock(spec=YrNoClient)
    return client


@pytest.fixture
def health_service(mock_yrno_client):
    """Create health service with mocked client"""
    startup_time = datetime.utcnow() - timedelta(hours=1)
    return HealthService(mock_yrno_client, startup_time)


@pytest.mark.asyncio
async def test_health_check_healthy(health_service, mock_yrno_client):
    """Test health check when all systems are operational"""
    mock_yrno_client.check_availability = AsyncMock(return_value=True)
    
    status = await health_service.check_health()
    
    assert status.status == "healthy"
    assert status.yrno_available is True
    assert status.uptime_seconds > 0
    assert status.version == "1.0.0"


@pytest.mark.asyncio
async def test_health_check_degraded(health_service, mock_yrno_client):
    """Test health check when yr.no is unavailable"""
    mock_yrno_client.check_availability = AsyncMock(return_value=False)
    
    status = await health_service.check_health()
    
    assert status.status == "degraded"
    assert status.yrno_available is False
    assert status.uptime_seconds > 0


@pytest.mark.asyncio
async def test_health_check_uptime(health_service, mock_yrno_client):
    """Test that uptime is calculated correctly"""
    mock_yrno_client.check_availability = AsyncMock(return_value=True)
    
    status = await health_service.check_health()
    
    # Should be approximately 1 hour (3600 seconds)
    assert 3500 <= status.uptime_seconds <= 3700


@pytest.mark.asyncio
async def test_health_check_cache_statistics(health_service, mock_yrno_client):
    """Test that cache statistics are included"""
    mock_yrno_client.check_availability = AsyncMock(return_value=True)
    
    status = await health_service.check_health()
    
    assert isinstance(status.cache_size, int)
    assert status.cache_size >= 0
