"""Pydantic models for API requests and responses"""

from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class TemperatureUnit(str, Enum):
    """Temperature measurement units"""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    
    def convert_from_celsius(self, temp_c: float) -> float:
        """Convert Celsius to this unit"""
        if self == TemperatureUnit.CELSIUS:
            return temp_c
        elif self == TemperatureUnit.FAHRENHEIT:
            return temp_c * 9/5 + 32
        return temp_c


class Location(BaseModel):
    """Geographic location"""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    name: Optional[str] = Field(None, description="Location name")
    
    @field_validator('latitude', 'longitude')
    @classmethod
    def truncate_coordinates(cls, v: float) -> float:
        """Truncate to 4 decimal places per yr.no requirements"""
        return float(f"{v:.4f}")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "latitude": 44.8125,
                    "longitude": 20.4612,
                    "name": "Belgrade, Serbia"
                }
            ]
        }
    }


class TemperatureReading(BaseModel):
    """Single temperature reading at specific date and time"""
    date: dt.date = Field(..., description="Forecast date")
    temperature: float = Field(..., description="Temperature value")
    unit: TemperatureUnit = Field(default=TemperatureUnit.CELSIUS, description="Temperature unit")
    time: dt.time = Field(..., description="Time of reading (closest to 14:00 local)")
    source_time: dt.datetime = Field(..., description="Original UTC timestamp from yr.no")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2026-01-15",
                    "temperature": 5.3,
                    "unit": "celsius",
                    "time": "14:00:00",
                    "source_time": "2026-01-15T13:00:00Z"
                }
            ]
        }
    }


class ForecastRequest(BaseModel):
    """Input model for temperature forecast requests"""
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate")
    location_name: Optional[str] = Field(None, min_length=2, max_length=200, description="Location name search")
    days: Optional[int] = Field(None, ge=1, le=10, description="Number of days to return")
    unit: TemperatureUnit = Field(default=TemperatureUnit.CELSIUS, description="Temperature unit")
    timezone: Optional[str] = Field(None, description="IANA timezone (e.g., 'Europe/Oslo'), auto-detected if not provided")
    
    @model_validator(mode='after')
    def validate_location(self):
        """Ensure either coordinates or location_name is provided, default to Belgrade"""
        has_coords = self.latitude is not None and self.longitude is not None
        has_name = self.location_name is not None
        
        if not has_coords and not has_name:
            # Use Belgrade default
            from app.core.config import settings
            self.latitude = settings.BELGRADE_LAT
            self.longitude = settings.BELGRADE_LON
        
        return self
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "latitude": 44.8125,
                    "longitude": 20.4612,
                    "days": 7,
                    "unit": "celsius"
                },
                {
                    "location_name": "Oslo",
                    "unit": "fahrenheit"
                }
            ]
        }
    }


class ForecastResponse(BaseModel):
    """Output model for temperature forecast responses"""
    location: Location = Field(..., description="Location details")
    forecasts: List[TemperatureReading] = Field(..., description="Temperature forecasts")
    days_returned: int = Field(..., description="Number of forecast days")
    cached: bool = Field(default=False, description="Data served from cache")
    stale: bool = Field(default=False, description="Cached data is stale (TTL expired)")
    cached_at: Optional[dt.datetime] = Field(None, description="When data was originally cached")
    generated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow, description="Response generation time")
    
    @field_validator('forecasts')
    @classmethod
    def sort_forecasts(cls, v: List[TemperatureReading]) -> List[TemperatureReading]:
        """Ensure forecasts are sorted by date"""
        return sorted(v, key=lambda x: x.date)
    
    @model_validator(mode='after')
    def validate_days_count(self):
        """Validate days_returned matches forecast count"""
        if self.forecasts:
            self.days_returned = len(self.forecasts)
        return self
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "location": {
                        "latitude": 44.8125,
                        "longitude": 20.4612,
                        "name": "Belgrade, Serbia"
                    },
                    "forecasts": [
                        {
                            "date": "2026-01-15",
                            "temperature": 5.3,
                            "unit": "celsius",
                            "time": "14:00:00",
                            "source_time": "2026-01-15T13:00:00Z"
                        }
                    ],
                    "days_returned": 1,
                    "cached": False,
                    "stale": False,
                    "generated_at": "2026-01-14T10:30:00Z"
                }
            ]
        }
    }


class HealthStatus(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    yrno_available: bool = Field(..., description="yr.no API reachable")
    cache_size: int = Field(..., description="Number of cached entries")
    cache_hit_rate: Optional[float] = Field(None, description="Cache hit rate (0-100)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "version": "1.0.0",
                    "uptime_seconds": 3600.5,
                    "yrno_available": True,
                    "cache_size": 15,
                    "cache_hit_rate": 85.5
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "InvalidCoordinates",
                    "message": "Latitude must be between -90 and 90",
                    "details": {"latitude": 100.5}
                }
            ]
        }
    }
