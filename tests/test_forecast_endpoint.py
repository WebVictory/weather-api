"""Tests for forecast endpoint"""

import pytest


def test_forecast_default_belgrade(client):
    """Test forecast endpoint defaults to Belgrade"""
    response = client.get("/api/forecast")

    assert response.status_code == 200
    data = response.json()

    assert "location" in data
    assert data["location"]["latitude"] == 44.8125
    assert data["location"]["longitude"] == 20.4612
    assert "forecasts" in data
    assert isinstance(data["forecasts"], list)


def test_forecast_with_coordinates(client):
    """Test forecast with explicit coordinates"""
    response = client.get("/api/forecast?lat=59.9139&lon=10.7522")

    assert response.status_code == 200
    data = response.json()

    assert data["location"]["latitude"] == 59.9139
    assert data["location"]["longitude"] == 10.7522


def test_forecast_invalid_latitude(client):
    """Test forecast with invalid latitude"""
    response = client.get("/api/forecast?lat=100&lon=20")

    assert response.status_code == 422  # Validation error


def test_forecast_invalid_longitude(client):
    """Test forecast with invalid longitude"""
    response = client.get("/api/forecast?lat=40&lon=200")

    assert response.status_code == 422  # Validation error


def test_forecast_with_unit_fahrenheit(client):
    """Test forecast with Fahrenheit unit"""
    response = client.get("/api/forecast?unit=fahrenheit")

    assert response.status_code == 200
    data = response.json()

    if data["forecasts"]:
        assert data["forecasts"][0]["unit"] == "fahrenheit"


def test_forecast_with_days_limit(client):
    """Test forecast with days limit"""
    response = client.get("/api/forecast?days=3")

    assert response.status_code == 200
    data = response.json()

    assert data["days_returned"] <= 3


def test_forecast_invalid_days(client):
    """Test forecast with invalid days parameter"""
    # Too low
    response = client.get("/api/forecast?days=0")
    assert response.status_code == 422

    # Too high
    response = client.get("/api/forecast?days=11")
    assert response.status_code == 422


def test_forecast_response_structure(client):
    """Test forecast response has correct structure"""
    response = client.get("/api/forecast")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "location" in data
    assert "forecasts" in data
    assert "days_returned" in data
    assert "cached" in data
    assert "generated_at" in data

    # Check location structure
    location = data["location"]
    assert "latitude" in location
    assert "longitude" in location

    # Check forecast structure (if any forecasts returned)
    if data["forecasts"]:
        forecast = data["forecasts"][0]
        assert "date" in forecast
        assert "temperature" in forecast
        assert "unit" in forecast
        assert "time" in forecast
        assert "source_time" in forecast


def test_root_endpoint(client):
    """Test root endpoint returns web interface"""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_docs_endpoint(client):
    """Test OpenAPI docs endpoint is accessible"""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema(client):
    """Test OpenAPI schema endpoint"""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert "/api/forecast" in schema["paths"]
