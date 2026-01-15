"""Configuration management"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""
    
    # Server
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Cache
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # yr.no API
    YR_NO_TIMEOUT_SECONDS: int = int(os.getenv("YR_NO_TIMEOUT_SECONDS", "10"))
    YR_NO_USER_AGENT: str = os.getenv(
        "YR_NO_USER_AGENT",
        "weather-api-demo/1.0 (github.com/user/weather-api)"
    )
    YR_NO_BASE_URL: str = "https://api.met.no/weatherapi/locationforecast/2.0"
    
    # Application
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_NAME: str = "Daily Temperature Service"
    APP_DESCRIPTION: str = "Weather forecast API powered by yr.no"
    
    # Belgrade default coordinates (truncated to 4 decimals)
    BELGRADE_LAT: float = 44.8125
    BELGRADE_LON: float = 20.4612
    
    # Time targeting
    TARGET_HOUR: int = 14
    TARGET_MINUTE: int = 0
    
    # Coordinate precision (yr.no requirement)
    COORDINATE_PRECISION: int = 4


settings = Settings()
