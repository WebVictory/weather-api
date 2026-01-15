"""Pytest configuration and shared fixtures"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client with lifespan events"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def belgrade_coords():
    """Belgrade coordinates"""
    return {
        "lat": 44.8125,
        "lon": 20.4612
    }


@pytest.fixture
def oslo_coords():
    """Oslo coordinates"""
    return {
        "lat": 59.9139,
        "lon": 10.7522
    }


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)
