"""Weather forecast service"""

from datetime import datetime, date, time
from typing import List, Optional
import asyncio
import httpx

from app.api.models import (
    Location,
    TemperatureReading,
    ForecastResponse,
    TemperatureUnit
)
from app.services.yrno_client import YrNoClient, YrNoTimeseriesEntry
from app.services.timezone_service import timezone_service
from app.core.cache import cache_manager, CacheEntry
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Lock for preventing thundering herd
fetch_locks = {}


class WeatherService:
    """Service for fetching and processing weather forecasts"""
    
    def __init__(self, yrno_client: YrNoClient):
        self.yrno_client = yrno_client
    
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
        days: Optional[int] = None,
        unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        timezone_override: Optional[str] = None
    ) -> ForecastResponse:
        """
        Get temperature forecast for location
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Optional location name
            days: Optional limit on number of days
            unit: Temperature unit
            timezone_override: Optional IANA timezone string
            
        Returns:
            ForecastResponse with temperature readings
        """
        # Truncate coordinates
        lat = float(f"{lat:.4f}")
        lon = float(f"{lon:.4f}")
        
        cache_key = cache_manager.generate_key(lat, lon)
        
        # Check cache first
        cached_entry = cache_manager.get(cache_key)
        if cached_entry:
            logger.info(f"Serving from cache: {cache_key}")
            response = cached_entry.data
            response.cached = True
            response.cached_at = cached_entry.created_at
            
            # Apply unit conversion if needed
            if unit != TemperatureUnit.CELSIUS:
                response = self._convert_units(response, unit)
            
            # Apply days filter if requested
            if days:
                response = self._filter_days(response, days)
            
            return response
        
        # Fetch from yr.no with thundering herd protection
        lock_key = f"lock:{cache_key}"
        if lock_key not in fetch_locks:
            fetch_locks[lock_key] = asyncio.Lock()
        
        async with fetch_locks[lock_key]:
            # Double-check cache after acquiring lock
            cached_entry = cache_manager.get(cache_key)
            if cached_entry:
                logger.info(f"Serving from cache after lock: {cache_key}")
                response = cached_entry.data
                response.cached = True
                response.cached_at = cached_entry.created_at
                
                if unit != TemperatureUnit.CELSIUS:
                    response = self._convert_units(response, unit)
                if days:
                    response = self._filter_days(response, days)
                
                return response
            
            # Fetch from yr.no
            try:
                timeseries = await self.yrno_client.fetch_forecast(lat, lon)
            except httpx.HTTPError as e:
                logger.error(f"yr.no API error: {e}")
                
                # Try stale cache
                stale_entry = cache_manager.get_stale(cache_key)
                if stale_entry:
                    logger.warning(f"Serving stale cache due to yr.no error: {cache_key}")
                    response = stale_entry.data
                    response.cached = True
                    response.stale = True
                    response.cached_at = stale_entry.created_at
                    
                    if unit != TemperatureUnit.CELSIUS:
                        response = self._convert_units(response, unit)
                    if days:
                        response = self._filter_days(response, days)
                    
                    return response
                
                # No cache available, raise error
                raise httpx.HTTPError(f"yr.no API unavailable: {e}")
            
            # Process forecast
            readings = self._process_timeseries(
                timeseries,
                lat,
                lon,
                timezone_override
            )
            
            # Build response
            location = Location(
                latitude=lat,
                longitude=lon,
                name=location_name
            )
            
            response = ForecastResponse(
                location=location,
                forecasts=readings,
                days_returned=len(readings),
                cached=False,
                generated_at=datetime.utcnow()
            )
            
            # Store in cache (always store as Celsius)
            cache_manager.set(cache_key, response)
            
            # Apply unit conversion if needed
            if unit != TemperatureUnit.CELSIUS:
                response = self._convert_units(response, unit)
            
            # Apply days filter if requested
            if days:
                response = self._filter_days(response, days)
            
            return response
    
    def _process_timeseries(
        self,
        timeseries: List[YrNoTimeseriesEntry],
        lat: float,
        lon: float,
        timezone_override: Optional[str]
    ) -> List[TemperatureReading]:
        """
        Process yr.no timeseries to extract ~14:00 temperatures
        
        Args:
            timeseries: List of yr.no timeseries entries
            lat: Latitude
            lon: Longitude
            timezone_override: Optional timezone override
            
        Returns:
            List of temperature readings at ~14:00 local time
        """
        readings_by_date = {}
        
        for entry in timeseries:
            utc_time = entry.time
            local_time = timezone_service.to_local_time(utc_time, lat, lon, timezone_override)
            
            forecast_date = local_time.date()
            temperature = entry.data.instant.details.air_temperature
            
            # Calculate time difference from 14:00
            target_time = datetime.combine(forecast_date, time(settings.TARGET_HOUR, settings.TARGET_MINUTE))
            target_time = target_time.replace(tzinfo=local_time.tzinfo)
            time_diff = abs((local_time - target_time).total_seconds())
            
            # Keep closest time to 14:00 for each date
            if forecast_date not in readings_by_date:
                readings_by_date[forecast_date] = {
                    "time_diff": time_diff,
                    "reading": TemperatureReading(
                        date=forecast_date,
                        temperature=temperature,
                        unit=TemperatureUnit.CELSIUS,
                        time=local_time.time(),
                        source_time=utc_time
                    )
                }
            else:
                if time_diff < readings_by_date[forecast_date]["time_diff"]:
                    readings_by_date[forecast_date] = {
                        "time_diff": time_diff,
                        "reading": TemperatureReading(
                            date=forecast_date,
                            temperature=temperature,
                            unit=TemperatureUnit.CELSIUS,
                            time=local_time.time(),
                            source_time=utc_time
                        )
                    }
        
        # Extract readings and sort by date
        readings = [item["reading"] for item in readings_by_date.values()]
        readings.sort(key=lambda r: r.date)
        
        logger.info(f"Processed {len(readings)} temperature readings at ~14:00")
        return readings
    
    def _convert_units(self, response: ForecastResponse, target_unit: TemperatureUnit) -> ForecastResponse:
        """Convert temperature units in response"""
        converted_forecasts = []
        for reading in response.forecasts:
            converted_temp = target_unit.convert_from_celsius(reading.temperature)
            converted_reading = reading.model_copy(
                update={
                    "temperature": converted_temp,
                    "unit": target_unit
                }
            )
            converted_forecasts.append(converted_reading)
        
        response.forecasts = converted_forecasts
        return response
    
    def _filter_days(self, response: ForecastResponse, days: int) -> ForecastResponse:
        """Filter response to specified number of days"""
        response.forecasts = response.forecasts[:days]
        response.days_returned = len(response.forecasts)
        return response
