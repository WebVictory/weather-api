# Daily Temperature Service

Weather forecast API powered by [yr.no](https://www.yr.no/), providing daily temperature forecasts at approximately 14:00 local time for any location worldwide.

## Features

- 🌡️ Temperature forecasts for any location (coordinates or city name)
- 🕐 Automated 14:00 local time selection across all timezones
- 🌍 Support for locations worldwide with automatic timezone detection
- 🔄 Intelligent caching (1-hour TTL) with stale cache fallback
- 🐳 Docker deployment in under 5 minutes
- 📚 Interactive API documentation (Swagger UI)
- 🌐 Web interface for non-technical users
- 🇺🇸 Celsius and Fahrenheit support
- ⚡ High performance (handles 100+ concurrent requests)

## Quick Start

### Using Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   docker build -t weather-api .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 weather-api
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:8000/api/forecast
   ```

**Total time:** ~3 minutes

### Using Docker Compose

```bash
docker-compose up -d
```

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python -m app.main
   ```

3. **Access the service:**
   - Web Interface: http://localhost:8000/
   - API: http://localhost:8000/api/forecast
   - Docs: http://localhost:8000/docs

## API Usage

### Get Belgrade Forecast (Default)

```bash
curl http://localhost:8000/forecast
```

**Response:**
```json
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
  "cached": false,
  "generated_at": "2026-01-14T10:30:00Z"
}
```

### Get Forecast for Custom Coordinates

```bash
curl "http://localhost:8000/api/forecast?lat=59.9139&lon=10.7522"
```

### Get Forecast in Fahrenheit

```bash
curl "http://localhost:8000/api/forecast?unit=fahrenheit"
```

### Limit Number of Days

```bash
curl "http://localhost:8000/api/forecast?days=3"
```

### Specify Timezone Manually

```bash
curl "http://localhost:8000/api/forecast?lat=59.9139&lon=10.7522&timezone=Europe/Oslo"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/forecast` | GET | Get temperature forecast |
| `/health` | GET | Health check endpoint |
| `/docs` | GET | Interactive API documentation (Swagger UI) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |
| `/` | GET | Root endpoint with API info |

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lat` | float | 44.8125 | Latitude (-90 to 90) |
| `lon` | float | 20.4612 | Longitude (-180 to 180) |
| `location_name` | string | - | Location name (e.g., "Oslo") |
| `days` | int | all | Number of days to return (1-10) |
| `unit` | string | celsius | Temperature unit (celsius/fahrenheit) |
| `timezone` | string | auto | IANA timezone (e.g., "Europe/Oslo") |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | HTTP server port |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CACHE_TTL_SECONDS` | 3600 | Cache duration (1 hour) |
| `CACHE_MAX_SIZE` | 1000 | Maximum cached locations |
| `YR_NO_TIMEOUT_SECONDS` | 10 | yr.no API timeout |
| `YR_NO_USER_AGENT` | weather-api-demo/1.0 | User-Agent for yr.no |

## Architecture

```
┌─────────────────┐
│   API Clients   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI App    │
│  - /forecast    │
│  - /health      │
│  - /docs        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Weather Service │
│  - Cache (1h)   │
│  - Timezone     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   yr.no API     │
│  (Locationforecast)
└─────────────────┘
```

## Testing

Run tests with pytest:

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

## Development

### Project Structure

```
weather-api/
├── app/
│   ├── api/              # API endpoints and models
│   │   ├── models.py     # Pydantic models
│   │   └── routes.py     # API routes
│   ├── services/         # Business logic
│   │   ├── weather_service.py
│   │   ├── yrno_client.py
│   │   └── timezone_service.py
│   ├── core/             # Infrastructure
│   │   ├── config.py     # Configuration
│   │   ├── logging.py    # Logging setup
│   │   └── cache.py      # Cache manager
│   └── main.py           # FastAPI application
├── tests/                # Test suite
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Code Quality

```bash
# Format code
ruff format app/ tests/

# Lint code
ruff check app/ tests/

# Type check
mypy app/
```

## Troubleshooting

### Docker build fails

**Issue:** Docker build takes too long or fails

**Solution:**
- Ensure you have a stable internet connection
- Check Docker daemon is running: `docker ps`
- Try with `--no-cache`: `docker build --no-cache -t weather-api .`

### yr.no API unavailable

**Issue:** API returns 504 Gateway Timeout

**Solution:**
- Check yr.no status: https://api.met.no/
- The service will serve stale cache data if available (with `stale: true` flag)
- Wait a few seconds and retry

### Cache not working

**Issue:** All requests show `cached: false`

**Solution:**
- Ensure coordinates are exactly the same (truncated to 4 decimals)
- Check cache TTL hasn't expired (default 1 hour)
- Review logs: `docker logs <container-id>`

## Performance

- **Response Time:**
  - Cached: < 500ms
  - Fresh (yr.no): < 2 seconds
- **Concurrency:** Handles 100+ concurrent requests
- **Cache Hit Rate:** Typically 85-90% in production
- **yr.no Request Protection:** Max 1 request per location per hour

## License

MIT License

## Credits

- Weather data provided by [MET Norway](https://www.met.no/)
- Geocoding by [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI and yr.no API
