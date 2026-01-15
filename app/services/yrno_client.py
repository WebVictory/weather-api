"""yr.no API client"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class YrNoInstantDetails(BaseModel):
    """yr.no instant weather details"""
    air_temperature: float
    cloud_area_fraction: Optional[float] = None
    wind_speed: Optional[float] = None


class YrNoInstant(BaseModel):
    """yr.no instant data"""
    details: YrNoInstantDetails


class YrNoTimeseriesData(BaseModel):
    """yr.no timeseries data"""
    instant: YrNoInstant
    next_1_hours: Optional[Dict[str, Any]] = None
    next_6_hours: Optional[Dict[str, Any]] = None


class YrNoTimeseriesEntry(BaseModel):
    """yr.no timeseries entry"""
    time: datetime
    data: YrNoTimeseriesData


class YrNoClient:
    """Client for yr.no Locationforecast API"""
    
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.base_url = settings.YR_NO_BASE_URL
    
    async def fetch_forecast(self, lat: float, lon: float) -> List[YrNoTimeseriesEntry]:
        """
        Fetch weather forecast from yr.no
        
        Args:
            lat: Latitude (truncated to 4 decimals)
            lon: Longitude (truncated to 4 decimals)
            
        Returns:
            List of timeseries entries with temperature data
            
        Raises:
            httpx.HTTPError: If request fails
        """
        # Truncate coordinates to 4 decimals (yr.no requirement)
        lat_str = f"{lat:.4f}"
        lon_str = f"{lon:.4f}"
        
        url = f"{self.base_url}/compact"
        params = {
            "lat": lat_str,
            "lon": lon_str,
        }
        
        logger.info(f"Fetching forecast from yr.no: lat={lat_str}, lon={lon_str}")
        
        response = await self.http_client.get(
            url,
            params=params,
            timeout=settings.YR_NO_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Parse timeseries
        timeseries_raw = data.get("properties", {}).get("timeseries", [])
        timeseries = [
            YrNoTimeseriesEntry(**entry)
            for entry in timeseries_raw
        ]
        
        logger.info(f"Received {len(timeseries)} forecast entries from yr.no")
        return timeseries
    
    async def check_availability(self) -> bool:
        """
        Check if yr.no API is available
        
        Returns:
            True if API is reachable, False otherwise
        """
        url = f"{self.base_url}/compact"
        params = {
            "lat": f"{settings.BELGRADE_LAT:.4f}",
            "lon": f"{settings.BELGRADE_LON:.4f}",
        }
        
        response = await self.http_client.get(
            url,
            params=params,
            timeout=5.0
        )
        return response.status_code == 200
