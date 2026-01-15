# Architecture Documentation

System design and architecture for the Daily Temperature Service.

## System Overview

The Daily Temperature Service is a FastAPI-based weather forecast application that provides daily temperature forecasts at approximately 14:00 local time for any location worldwide. It uses the yr.no Locationforecast API as its data source.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
│  - HTTP/REST Clients (curl, browsers, apps)            │
│  - Web Interface (HTML/CSS)                             │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Application                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           API Layer (app/api/)                   │  │
│  │  - routes.py: REST endpoints                     │  │
│  │  - web_routes.py: Web interface                  │  │
│  │  - models.py: Pydantic data models               │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────────┐  │
│  │        Business Logic (app/services/)            │  │
│  │  - weather_service.py: Forecast orchestration    │  │
│  │  - location_service.py: Geocoding                │  │
│  │  - health_service.py: Health checks              │  │
│  │  - yrno_client.py: yr.no API client              │  │
│  │  - timezone_service.py: Timezone handling        │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────────┐  │
│  │       Infrastructure (app/core/)                 │  │
│  │  - config.py: Configuration management           │  │
│  │  - logging.py: Structured logging                │  │
│  │  - cache.py: TTL cache manager                   │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                          │
│  - yr.no Locationforecast API (weather data)            │
│  - Nominatim/OSM (geocoding)                            │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### API Layer

**Responsibilities:**
- HTTP request/response handling
- Input validation (Pydantic models)
- Error handling and HTTP status codes
- OpenAPI schema generation

**Key Files:**
- `app/api/routes.py` - REST API endpoints
- `app/api/web_routes.py` - Web interface routes
- `app/api/models.py` - Pydantic models for validation

**Endpoints:**
- `GET /forecast` - Temperature forecast
- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /web/` - Web interface
- `POST /web/forecast` - Web form submission

### Business Logic Layer

**Responsibilities:**
- Weather data processing
- Time-of-day filtering (~14:00)
- Temperature unit conversion
- Location resolution (geocoding)
- Cache management
- Timezone handling

**Key Services:**

#### WeatherService
- Orchestrates forecast retrieval
- Handles caching with TTL
- Filters timeseries for ~14:00 local time
- Converts temperature units
- Implements thundering herd protection

#### LocationService
- Geocodes location names to coordinates
- Uses Nominatim (OpenStreetMap)
- Caches results for 24 hours
- Handles rate limiting (1 req/s)

#### YrNoClient
- Async HTTP client for yr.no API
- Parses GeoJSON response
- Truncates coordinates to 4 decimals
- Timeout and error handling

#### TimezoneService
- Auto-detects timezone from coordinates
- Converts UTC to local time
- Handles DST transitions
- Supports manual timezone override

#### HealthService
- Checks yr.no API availability
- Calculates uptime
- Reports cache statistics

### Infrastructure Layer

**Responsibilities:**
- Configuration management
- Structured logging
- Cache implementation
- Startup/shutdown lifecycle

**Key Components:**

#### Configuration (config.py)
- Environment variable loading
- Default values
- Application constants

#### Logging (logging.py)
- JSON structured logs
- Configurable log levels
- UTC timestamps

#### Cache (cache.py)
- TTLCache with 1-hour expiration
- Stale cache fallback
- Statistics tracking
- Thundering herd protection

## Data Flow

### Forecast Request Flow

```
1. Client Request
   ↓
2. FastAPI Route Handler
   ↓
3. Pydantic Validation
   ↓
4. Weather Service
   ↓
5. Check Cache ──→ Cache Hit ──→ Return Cached Data
   │
   ↓ Cache Miss
   │
6. Acquire Lock (prevent duplicate requests)
   ↓
7. Double-Check Cache
   ↓
8. yr.no API Call
   │
   ├──→ Success ──→ Process & Cache
   │
   └──→ Failure ──→ Check Stale Cache
                     │
                     ├──→ Found ──→ Return Stale Data
                     │
                     └──→ Not Found ──→ 504 Error
```

### Geocoding Flow

```
1. Location Name Provided
   ↓
2. Location Service
   ↓
3. Check Cache ──→ Cache Hit ──→ Return Coordinates
   │
   ↓ Cache Miss
   │
4. Nominatim API Call
   │
   ├──→ Found ──→ Cache & Return
   │
   └──→ Not Found ──→ 404 Error
```

### Time Filtering Algorithm

```
1. Receive yr.no timeseries (UTC timestamps)
   ↓
2. For each timestamp:
   │
   ├─→ Convert UTC to local time (using timezone)
   │
   ├─→ Group by date
   │
   └─→ Calculate time difference from 14:00
       │
       └─→ Keep entry closest to 14:00 per date
```

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.109+ | Web framework |
| Runtime | Python | 3.11+ | Programming language |
| Server | Uvicorn | 0.27+ | ASGI server |
| HTTP Client | httpx | 0.26+ | Async HTTP requests |
| Validation | Pydantic | 2.5+ | Data validation |

### Services

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Caching | cachetools | In-memory TTL cache |
| Geocoding | geopy + Nominatim | Location search |
| Timezone | timezonefinder + pytz | Timezone detection |
| Templates | Jinja2 | HTML rendering |

### Development

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Testing | pytest | Test framework |
| Linting | ruff | Code quality |
| Type Checking | mypy | Static type analysis |

## Deployment Architecture

### Docker Container

```
┌─────────────────────────────────────┐
│   Docker Container (python:3.11)   │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Uvicorn (Port 8000)        │  │
│  └────────────┬─────────────────┘  │
│               │                     │
│  ┌────────────▼─────────────────┐  │
│  │   FastAPI Application        │  │
│  │   - In-memory cache          │  │
│  │   - No external dependencies │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

**Characteristics:**
- Single container deployment
- No database required
- No external cache (Redis/Memcached)
- Stateless (cache lost on restart)
- Horizontal scaling possible (independent caches)

### Environment Configuration

```bash
# Server
PORT=8000

# Logging
LOG_LEVEL=INFO

# Cache
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# yr.no API
YR_NO_TIMEOUT_SECONDS=10
YR_NO_USER_AGENT=weather-api-demo/1.0 (...)

# Application
APP_VERSION=1.0.0
```

## Performance Characteristics

### Latency

| Scenario | Expected Latency | Notes |
|----------|------------------|-------|
| Cache Hit | < 500ms | In-memory cache lookup |
| Cache Miss (yr.no) | < 2s | Network + processing |
| Geocoding (cached) | < 50ms | In-memory lookup |
| Geocoding (fresh) | < 1s | Nominatim API call |

### Throughput

- **Concurrent Requests:** 100+ supported
- **Cache Hit Rate:** Typically 85-90%
- **yr.no Request Rate:** Max 1 per location per hour

### Caching Strategy

**Benefits:**
- Reduces yr.no API load
- Improves response times
- Provides fallback during outages

**Trade-offs:**
- Data may be up to 1 hour old
- Cache lost on restart
- Memory usage scales with unique locations

## Security Considerations

### Input Validation

- All API inputs validated via Pydantic
- Coordinate ranges enforced (-90 to 90, -180 to 180)
- String lengths limited
- No SQL injection risk (no database)

### yr.no API Protection

- Rate limiting via caching
- User-Agent header identification
- Respect ToS and rate limits
- Stale cache fallback prevents abuse

### Container Security

- Non-root user (appuser)
- Minimal base image (python:3.11-slim)
- No sensitive data in environment variables
- Health check for monitoring

## Monitoring & Observability

### Logging

**Log Format:** JSON structured logs

**Log Levels:**
- `INFO` - Normal operations (API requests, cache hits/misses)
- `WARNING` - Degraded state (stale cache, slow responses)
- `ERROR` - Failures (yr.no errors, exceptions)
- `DEBUG` - Detailed debugging

**Example Log Entry:**
```json
{
  "timestamp": "2026-01-14T10:30:00Z",
  "level": "INFO",
  "logger": "app.services.weather_service",
  "message": "Cache hit: forecast:59.9139:10.7522"
}
```

### Health Checks

**Endpoint:** `GET /health`

**Checks:**
- yr.no API connectivity
- Application uptime
- Cache size and hit rate

**Docker Health Check:**
```bash
curl -f http://localhost:8000/ || exit 1
```

### Metrics (Future Enhancement)

Potential metrics to track:
- Request count and latency (p50, p95, p99)
- Cache hit/miss ratio
- yr.no API call frequency
- Error rates by type
- Geocoding success rate

## Scalability

### Horizontal Scaling

**Pros:**
- Stateless application design
- Independent caches per instance
- Load balancer compatible

**Cons:**
- Cache not shared (multiple yr.no calls for same location)
- Increased yr.no API usage

**Recommendation:**
- Scale horizontally for high traffic
- Consider shared cache (Redis) for large deployments

### Vertical Scaling

**Resources:**
- CPU: Minimal (async I/O bound)
- Memory: ~100MB + (1KB × cached locations)
- Network: Dependent on yr.no API calls

## Design Decisions

### Why In-Memory Cache?

**Pros:**
- Simplest deployment (no external dependencies)
- Fastest access (0ms network latency)
- Aligns with specification requirements

**Cons:**
- Cache lost on restart
- Not shared across instances

**Decision:** In-memory cache chosen for simplicity and alignment with demo/MVP requirements. Production deployments may benefit from Redis.

### Why FastAPI?

**Pros:**
- Auto OpenAPI generation
- Native async support
- High performance
- Type-safe with Pydantic

**Cons:**
- Newer ecosystem than Flask/Django

**Decision:** FastAPI chosen for automatic API documentation and async capabilities.

### Why Nominatim?

**Pros:**
- Free and open-source
- No API key required
- Good coverage

**Cons:**
- 1 req/s rate limit
- Community-run infrastructure

**Decision:** Nominatim chosen for zero-setup geocoding. Production may use paid service (Google, Mapbox).

## Future Enhancements

### Potential Improvements

1. **Shared Cache (Redis)**
   - Share cache across instances
   - Persistent cache across restarts

2. **Metrics & Monitoring**
   - Prometheus metrics endpoint
   - Grafana dashboards

3. **Database Integration**
   - Historical forecast storage
   - User preferences

4. **Advanced Features**
   - Email/SMS alerts
   - Webhook notifications
   - Custom time selection (not just 14:00)

5. **Performance Optimizations**
   - Connection pooling
   - Response compression
   - CDN for web interface

## Development Guidelines

### Adding New Features

1. Define Pydantic models in `app/api/models.py`
2. Implement business logic in `app/services/`
3. Add API endpoints in `app/api/routes.py`
4. Write tests in `tests/`
5. Update documentation

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to public functions
- Keep functions focused and testable

### Testing Strategy

- **Unit Tests:** Business logic and models
- **Integration Tests:** API endpoints with mocked external services
- **End-to-End Tests:** Full request/response cycle

---

**Architecture Version:** 1.0  
**Last Updated:** 2026-01-14
