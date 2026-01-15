"""Location geocoding service"""

from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from cachetools import TTLCache

from app.core.logging import get_logger

logger = get_logger(__name__)


class LocationService:
    """Service for geocoding location names to coordinates"""
    
    def __init__(self):
        self.geolocator = Nominatim(
            user_agent="weather-api-demo/1.0",
            timeout=10
        )
        # Cache location searches for 24 hours
        self.cache: TTLCache = TTLCache(maxsize=500, ttl=86400)
    
    async def geocode(self, location_name: str) -> Optional[Tuple[float, float, str]]:
        """
        Geocode location name to coordinates
        
        Args:
            location_name: Location name to search
            
        Returns:
            Tuple of (latitude, longitude, display_name) or None if not found
        """
        # Check cache first
        cache_key = location_name.lower().strip()
        if cache_key in self.cache:
            logger.debug(f"Location cache hit: {location_name}")
            return self.cache[cache_key]
        
        logger.info(f"Geocoding location: {location_name}")
        
        try:
            # Rate limiting is handled internally by geopy
            location = self.geolocator.geocode(location_name)
            
            if location is None:
                logger.warning(f"Location not found: {location_name}")
                self.cache[cache_key] = None
                return None
            
            result = (
                float(f"{location.latitude:.4f}"),
                float(f"{location.longitude:.4f}"),
                location.address
            )
            
            # Cache result
            self.cache[cache_key] = result
            logger.info(f"Geocoded {location_name} to {result[0]}, {result[1]}")
            
            return result
        
        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for: {location_name}")
            return None
        
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            return None
    
    def get_cache_statistics(self) -> dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl_seconds": self.cache.ttl
        }


# Global location service instance
location_service = LocationService()
