"""API routes"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.models import (
    ForecastResponse,
    TemperatureUnit,
    HealthStatus,
    ErrorResponse
)
from app.services.weather_service import WeatherService
from app.services.yrno_client import YrNoClient
from app.services.health_service import HealthService
from app.services.location_service import location_service
from app.core.config import settings
from app.core.logging import get_logger
from app.main import app

logger = get_logger(__name__)

router = APIRouter()


def get_yrno_client() -> YrNoClient:
    """Get yr.no client dependency"""
    return YrNoClient(app.state.http_client)


def get_weather_service(yrno_client: YrNoClient = Depends(get_yrno_client)) -> WeatherService:
    """Get weather service dependency"""
    return WeatherService(yrno_client)


def get_health_service(yrno_client: YrNoClient = Depends(get_yrno_client)) -> HealthService:
    """Get health service dependency"""
    return HealthService(yrno_client, app.state.startup_time)


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Location not found"},
        504: {"model": ErrorResponse, "description": "yr.no API unavailable"}
    },
    summary="Get temperature forecast",
    description="Retrieve daily temperature forecasts at ~14:00 local time"
)
async def get_forecast(
    lat: Optional[float] = Query(
        None,
        ge=-90.0,
        le=90.0,
        description="Latitude coordinate"
    ),
    lon: Optional[float] = Query(
        None,
        ge=-180.0,
        le=180.0,
        description="Longitude coordinate"
    ),
    location_name: Optional[str] = Query(
        None,
        min_length=2,
        max_length=200,
        description="Location name (requires geocoding)"
    ),
    days: Optional[int] = Query(
        None,
        ge=1,
        le=10,
        description="Number of days to return"
    ),
    unit: TemperatureUnit = Query(
        TemperatureUnit.CELSIUS,
        description="Temperature unit"
    ),
    timezone: Optional[str] = Query(
        None,
        description="IANA timezone (e.g., 'Europe/Oslo'), auto-detected if not provided"
    ),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get temperature forecast for a location
    
    - If no coordinates or location_name provided, defaults to Belgrade, Serbia
    - Returns temperatures at approximately 14:00 local time
    - Forecasts are sorted by date (oldest to newest)
    """
    # Default to Belgrade if no location provided
    if lat is None and lon is None and location_name is None:
        lat = settings.BELGRADE_LAT
        lon = settings.BELGRADE_LON
        location_name = "Belgrade, Serbia"
        logger.info("Using default location: Belgrade")
    
    # Validate coordinates if provided
    if lat is not None and lon is not None:
        logger.info(f"Fetching forecast for coordinates: lat={lat}, lon={lon}")
        
        try:
            response = await weather_service.get_forecast(
                lat=lat,
                lon=lon,
                location_name=location_name,
                days=days,
                unit=unit,
                timezone_override=timezone
            )
            return response
        
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            raise HTTPException(
                status_code=504,
                detail="Unable to fetch forecast from yr.no"
            )
    
    # If location_name provided but coordinates not, use geocoding
    if location_name and (lat is None or lon is None):
        logger.info(f"Geocoding location: {location_name}")
        
        geocode_result = await location_service.geocode(location_name)
        
        if geocode_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Location not found: '{location_name}'. Please try a different search term or use coordinates."
            )
        
        lat, lon, display_name = geocode_result
        location_name = display_name
        
        logger.info(f"Geocoded to: {lat}, {lon} ({display_name})")
        
        try:
            response = await weather_service.get_forecast(
                lat=lat,
                lon=lon,
                location_name=location_name,
                days=days,
                unit=unit,
                timezone_override=timezone
            )
            return response
        
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            raise HTTPException(
                status_code=504,
                detail="Unable to fetch forecast from yr.no"
            )
    
    raise HTTPException(
        status_code=400,
        detail="Either coordinates (lat, lon) or location_name must be provided"
    )


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health check",
    description="Check service health status and yr.no API availability"
)
async def health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """
    Health check endpoint
    
    Returns:
    - status: "healthy" (all systems operational) or "degraded" (yr.no unavailable but cache working)
    - yrno_available: Boolean indicating yr.no API reachability
    - uptime_seconds: Time since service started
    - cache_size: Number of cached locations
    - cache_hit_rate: Percentage of requests served from cache
    
    Note: Always returns HTTP 200 OK. Check 'status' field for actual health status.
    """
    return await health_service.check_health()
