"""Timezone detection and conversion service"""

from datetime import datetime
from typing import Optional
import pytz
from timezonefinder import TimezoneFinder

from app.core.logging import get_logger

logger = get_logger(__name__)


class TimezoneService:
    """Service for timezone detection and time conversion"""
    
    def __init__(self):
        self.tf = TimezoneFinder()
    
    def get_timezone(self, lat: float, lon: float, tz_override: Optional[str] = None) -> pytz.timezone:
        """
        Get timezone for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            tz_override: Optional IANA timezone string to override auto-detection
            
        Returns:
            pytz timezone object
        """
        if tz_override:
            try:
                tz = pytz.timezone(tz_override)
                logger.debug(f"Using override timezone: {tz_override}")
                return tz
            except pytz.exceptions.UnknownTimeZoneError:
                logger.warning(f"Invalid timezone override: {tz_override}, falling back to auto-detection")
        
        # Auto-detect timezone from coordinates
        tz_str = self.tf.timezone_at(lat=lat, lng=lon)
        
        if not tz_str:
            # Fallback to UTC for ocean/polar coordinates
            logger.warning(f"Could not determine timezone for lat={lat}, lon={lon}, using UTC")
            return pytz.UTC
        
        logger.debug(f"Detected timezone: {tz_str} for lat={lat}, lon={lon}")
        return pytz.timezone(tz_str)
    
    def to_local_time(
        self,
        utc_time: datetime,
        lat: float,
        lon: float,
        tz_override: Optional[str] = None
    ) -> datetime:
        """
        Convert UTC time to local time for coordinates
        
        Args:
            utc_time: UTC datetime
            lat: Latitude
            lon: Longitude
            tz_override: Optional IANA timezone string
            
        Returns:
            Local datetime
        """
        tz = self.get_timezone(lat, lon, tz_override)
        
        # Ensure UTC time is timezone-aware
        if utc_time.tzinfo is None:
            utc_time = pytz.UTC.localize(utc_time)
        
        local_time = utc_time.astimezone(tz)
        return local_time
    
    def validate_timezone(self, tz_str: str) -> bool:
        """
        Validate IANA timezone string
        
        Args:
            tz_str: IANA timezone string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            pytz.timezone(tz_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False


# Global timezone service instance
timezone_service = TimezoneService()
