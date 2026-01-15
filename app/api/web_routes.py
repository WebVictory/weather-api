"""Web interface routes"""

from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.weather_service import WeatherService
from app.services.yrno_client import YrNoClient
from app.services.location_service import location_service
from app.api.models import TemperatureUnit
from app.core.config import settings
from app.core.logging import get_logger
from app.main import app

logger = get_logger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_yrno_client() -> YrNoClient:
    """Get yr.no client dependency"""
    return YrNoClient(app.state.http_client)


def get_weather_service(yrno_client: YrNoClient = Depends(get_yrno_client)) -> WeatherService:
    """Get weather service dependency"""
    return WeatherService(yrno_client)


@router.get("/", response_class=HTMLResponse)
async def web_index(request: Request):
    """Web interface home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/forecast", response_class=HTMLResponse)
async def web_forecast(
    request: Request,
    location_name: Optional[str] = Form(None),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    days: Optional[str] = Form(None),
    unit: str = Form("celsius"),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """Web interface forecast results"""
    try:
        # Convert empty strings to None and parse values
        location_name = location_name.strip() if location_name and location_name.strip() else None
        lat_float = float(latitude) if latitude and latitude.strip() else None
        lon_float = float(longitude) if longitude and longitude.strip() else None
        days_int = int(days) if days and days.strip() else None
        # Convert unit string to enum
        temp_unit = TemperatureUnit.CELSIUS if unit == "celsius" else TemperatureUnit.FAHRENHEIT

        # Default to Belgrade if no location provided
        if not location_name and lat_float is None and lon_float is None:
            lat_float = settings.BELGRADE_LAT
            lon_float = settings.BELGRADE_LON
            location_name = "Belgrade, Serbia"

        # Validate coordinates if provided
        if lat_float is not None and lon_float is not None:
            if not (-90 <= lat_float <= 90):
                return templates.TemplateResponse(
                    "forecast.html",
                    {
                        "request": request,
                        "error": f"Invalid latitude: {lat_float}. Must be between -90 and 90."
                    }
                )

            if not (-180 <= lon_float <= 180):
                return templates.TemplateResponse(
                    "forecast.html",
                    {
                        "request": request,
                        "error": f"Invalid longitude: {lon_float}. Must be between -180 and 180."
                    }
                )

            # Get forecast
            response = await weather_service.get_forecast(
                lat=lat_float,
                lon=lon_float,
                location_name=location_name,
                days=days_int,
                unit=temp_unit
            )

            return templates.TemplateResponse(
                "forecast.html",
                {
                    "request": request,
                    "location": response.location,
                    "forecasts": response.forecasts,
                    "days_returned": response.days_returned,
                    "cached": response.cached,
                    "stale": response.stale,
                    "error": None
                }
            )

        # Location name provided but no coordinates - use geocoding
        if location_name:
            geocode_result = await location_service.geocode(location_name)

            if geocode_result is None:
                return templates.TemplateResponse(
                    "forecast.html",
                    {
                        "request": request,
                        "error": f"Location not found: '{location_name}'. Please try a different search term."
                    }
                )

            lat_float, lon_float, display_name = geocode_result
            location_name = display_name

            # Get forecast with geocoded coordinates
            response = await weather_service.get_forecast(
                lat=lat_float,
                lon=lon_float,
                location_name=location_name,
                days=days_int,
                unit=temp_unit
            )

            return templates.TemplateResponse(
                "forecast.html",
                {
                    "request": request,
                    "location": response.location,
                    "forecasts": response.forecasts,
                    "days_returned": response.days_returned,
                    "cached": response.cached,
                    "stale": response.stale,
                    "error": None
                }
            )

        return templates.TemplateResponse(
            "forecast.html",
            {
                "request": request,
                "error": "Please provide either coordinates or location name."
            }
        )

    except Exception as e:
        logger.error(f"Web forecast error: {e}")
        return templates.TemplateResponse(
            "forecast.html",
            {
                "request": request,
                "error": f"Failed to fetch forecast: {str(e)}"
            }
        )
