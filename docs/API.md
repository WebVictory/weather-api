# API Documentation

Complete API reference for the Daily Temperature Service.

## Base URL

```
http://localhost:8000
```

## Interfaces

The service provides two interfaces:

- **Web Interface**: http://localhost:8000/ - User-friendly web form for getting forecasts
- **REST API**: http://localhost:8000/api/ - Programmatic access with JSON responses
- **Documentation**:
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

## Authentication

No authentication required. This is a public API.

## API Endpoints

### GET /api/forecast

Get temperature forecast for a location at approximately 14:00 local time.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `lat` | float | No | 44.8125 | Latitude coordinate (-90 to 90) |
| `lon` | float | No | 20.4612 | Longitude coordinate (-180 to 180) |
| `location_name` | string | No | - | Location name (e.g., "Oslo", "New York") |
| `days` | integer | No | all | Number of days to return (1-10) |
| `unit` | string | No | celsius | Temperature unit: "celsius" or "fahrenheit" |
| `timezone` | string | No | auto | IANA timezone (e.g., "Europe/Oslo") |

**Response:** `ForecastResponse`

**Status Codes:**
- `200 OK` - Forecast retrieved successfully
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Location not found (when using location_name)
- `504 Gateway Timeout` - yr.no API unavailable and no cache available

**Example Request:**

```bash
curl "http://localhost:8000/api/forecast?lat=59.9139&lon=10.7522&unit=fahrenheit&days=3"
```

**Example Response:**

```json
{
  "location": {
    "latitude": 59.9139,
    "longitude": 10.7522,
    "name": "Oslo, Norway"
  },
  "forecasts": [
    {
      "date": "2026-01-15",
      "temperature": 41.54,
      "unit": "fahrenheit",
      "time": "14:00:00",
      "source_time": "2026-01-15T13:00:00Z"
    },
    {
      "date": "2026-01-16",
      "temperature": 43.16,
      "unit": "fahrenheit",
      "time": "14:00:00",
      "source_time": "2026-01-16T13:00:00Z"
    }
  ],
  "days_returned": 2,
  "cached": true,
  "stale": false,
  "cached_at": "2026-01-15T10:00:00Z",
  "generated_at": "2026-01-15T10:30:00Z"
}
```

**Caching Behavior:**
- Responses are cached for 1 hour per location
- `cached: true` indicates data was served from cache
- `stale: true` indicates cache expired but yr.no unavailable (fallback mode)
- `cached_at` shows when data was originally fetched

---

### GET /health

Check service health status.

**Response:** `HealthStatus`

**Status Codes:**
- `200 OK` - Always returns 200 (check `status` field for actual health)

**Example Request:**

```bash
curl "http://localhost:8000/health"
```

**Example Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "yrno_available": true,
  "cache_size": 15,
  "cache_hit_rate": 85.5
}
```

**Status Values:**
- `healthy` - All systems operational
- `degraded` - yr.no API unavailable but service functional with cache
- `unhealthy` - Service cannot respond (should not see this in practice)

---

### GET /docs

Interactive API documentation (Swagger UI).

**Response:** HTML page with interactive API documentation

Access at: http://localhost:8000/docs

---

### GET /redoc

Alternative API documentation (ReDoc).

**Response:** HTML page with API documentation

Access at: http://localhost:8000/redoc

---

### GET /

Root endpoint with API information.

**Response:**

```json
{
  "name": "Daily Temperature Service",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### GET /web

Web interface home page.

**Response:** HTML form for forecast search

Access at: http://localhost:8000/web/

---

### POST /web/forecast

Web interface forecast results (form submission).

**Form Parameters:**
- `location_name` (optional)
- `latitude` (optional)
- `longitude` (optional)
- `days` (optional)
- `unit` (optional, default: celsius)

**Response:** HTML page with forecast results

---

## Data Models

### Location

```json
{
  "latitude": 44.8125,
  "longitude": 20.4612,
  "name": "Belgrade, Serbia"
}
```

**Fields:**
- `latitude` (float): Latitude coordinate, truncated to 4 decimals
- `longitude` (float): Longitude coordinate, truncated to 4 decimals
- `name` (string, optional): Human-readable location name

---

### TemperatureReading

```json
{
  "date": "2026-01-15",
  "temperature": 5.3,
  "unit": "celsius",
  "time": "14:00:00",
  "source_time": "2026-01-15T13:00:00Z"
}
```

**Fields:**
- `date` (string, ISO 8601): Forecast date
- `temperature` (float): Temperature value
- `unit` (string): Temperature unit ("celsius" or "fahrenheit")
- `time` (string, HH:MM:SS): Local time of reading (closest to 14:00)
- `source_time` (string, ISO 8601): Original UTC timestamp from yr.no

---

### ForecastResponse

```json
{
  "location": { ... },
  "forecasts": [ ... ],
  "days_returned": 7,
  "cached": true,
  "stale": false,
  "cached_at": "2026-01-15T10:00:00Z",
  "generated_at": "2026-01-15T10:30:00Z"
}
```

**Fields:**
- `location` (Location): Location details
- `forecasts` (array[TemperatureReading]): Temperature forecasts, sorted by date
- `days_returned` (integer): Number of forecast days
- `cached` (boolean): Whether data was served from cache
- `stale` (boolean): Whether cached data is expired (fallback mode)
- `cached_at` (string, ISO 8601, optional): When data was originally cached
- `generated_at` (string, ISO 8601): Response generation timestamp

---

### HealthStatus

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "yrno_available": true,
  "cache_size": 15,
  "cache_hit_rate": 85.5
}
```

**Fields:**
- `status` (string): Overall health status
- `version` (string): Application version
- `uptime_seconds` (float): Uptime since startup
- `yrno_available` (boolean): yr.no API connectivity status
- `cache_size` (integer): Number of cached locations
- `cache_hit_rate` (float, optional): Cache hit percentage (0-100)

---

### ErrorResponse

```json
{
  "error": "InvalidCoordinates",
  "message": "Latitude must be between -90 and 90",
  "details": {
    "latitude": 100.5
  }
}
```

**Fields:**
- `error` (string): Error code/type
- `message` (string): Human-readable error message
- `details` (object, optional): Additional error context

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Location not found |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded (yr.no) |
| 504 | Gateway Timeout - yr.no API unavailable |
| 500 | Internal Server Error - Unexpected error |

### Common Error Scenarios

**Invalid Coordinates:**
```bash
GET /forecast?lat=100&lon=20
```
→ `422 Unprocessable Entity`

**Location Not Found:**
```bash
GET /forecast?location_name=Atlantis
```
→ `404 Not Found`

**yr.no API Unavailable (with cache):**
```bash
GET /forecast?lat=59.9139&lon=10.7522
```
→ `200 OK` with `stale: true`

**yr.no API Unavailable (no cache):**
```bash
GET /forecast?lat=12.3456&lon=78.9012
```
→ `504 Gateway Timeout`

---

## Rate Limiting

- **Incoming requests:** No rate limiting on API endpoints
- **yr.no API protection:** Automatic caching prevents excessive yr.no requests
  - 1 request per location per hour max
  - Stale cache served if yr.no unavailable
- **Geocoding:** 1 request per second (Nominatim limit)
  - Results cached for 24 hours

---

## Caching

### Cache Strategy

- **TTL:** 1 hour (3600 seconds)
- **Max Size:** 1000 locations
- **Stale Cache:** Served when yr.no unavailable
- **Cache Key:** Location coordinates (4 decimal precision)

### Cache Headers

The API does not use HTTP cache headers. Caching is transparent and indicated by the `cached` field in responses.

---

## Examples

### Default Belgrade Forecast

```bash
curl http://localhost:8000/api/forecast
```

### Oslo in Fahrenheit

```bash
curl "http://localhost:8000/api/forecast?location_name=Oslo&unit=fahrenheit"
```

### New York, Next 3 Days

```bash
curl "http://localhost:8000/api/forecast?lat=40.7128&lon=-74.0060&days=3"
```

### Tokyo with Custom Timezone

```bash
curl "http://localhost:8000/api/forecast?lat=35.6762&lon=139.6503&timezone=Asia/Tokyo"
```

### Using Python

```python
import requests

response = requests.get(
    "http://localhost:8000/api/forecast",
    params={
        "location_name": "Oslo",
        "unit": "fahrenheit",
        "days": 5
    }
)

data = response.json()
print(f"Location: {data['location']['name']}")
print(f"Days returned: {data['days_returned']}")

for forecast in data['forecasts']:
    print(f"{forecast['date']}: {forecast['temperature']}°{forecast['unit']}")
```

### Using JavaScript

```javascript
fetch('http://localhost:8000/api/forecast?location_name=Oslo&unit=celsius')
  .then(response => response.json())
  .then(data => {
    console.log(`Location: ${data.location.name}`);
    data.forecasts.forEach(forecast => {
      console.log(`${forecast.date}: ${forecast.temperature}°C`);
    });
  });
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- JSON: http://localhost:8000/openapi.json
- Interactive UI: http://localhost:8000/docs

---

## Support

For issues or questions:
- GitHub Issues: [github.com/user/weather-api/issues]
- API Docs: http://localhost:8000/docs
