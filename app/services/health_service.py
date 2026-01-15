"""Health check service"""

from datetime import datetime

from app.api.models import HealthStatus
from app.services.yrno_client import YrNoClient
from app.core.cache import cache_manager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """Service for health checks"""
    
    def __init__(self, yrno_client: YrNoClient, startup_time: datetime):
        self.yrno_client = yrno_client
        self.startup_time = startup_time
    
    async def check_health(self) -> HealthStatus:
        """
        Perform health check
        
        Returns:
            HealthStatus with service status
        """
        # Check yr.no availability
        yrno_available = await self._check_yrno()
        
        # Calculate uptime
        uptime = (datetime.utcnow() - self.startup_time).total_seconds()
        
        # Get cache statistics
        cache_stats = cache_manager.get_statistics()
        
        # Determine overall status
        if yrno_available:
            status = "healthy"
        else:
            status = "degraded"  # Still functional with cache
        
        return HealthStatus(
            status=status,
            version=settings.APP_VERSION,
            uptime_seconds=uptime,
            yrno_available=yrno_available,
            cache_size=cache_stats["size"],
            cache_hit_rate=cache_stats["hit_rate"]
        )
    
    async def _check_yrno(self) -> bool:
        """Check if yr.no API is available"""
        try:
            available = await self.yrno_client.check_availability()
            return available
        except Exception as e:
            logger.warning(f"yr.no health check failed: {e}")
            return False
