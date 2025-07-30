# SparkJAR Crews API Service

This FastAPI service provides HTTP endpoints for executing CrewAI crews remotely. It's designed to be called by the main API gateway to execute crews in a distributed architecture.

## Features

- **HTTP API**: RESTful endpoints for crew execution
- **JWT Authentication**: Secure token-based authentication with scope validation
- **Request Tracing**: Distributed tracing with request IDs
- **Structured Logging**: JSON logging in production, human-readable in development
- **Health Checks**: Service health monitoring endpoint
- **Error Handling**: Comprehensive error handling and reporting
- **CORS Support**: Configurable CORS for cross-origin requests

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status and available crews. No authentication required.

**Response:**
```json
{
  "status": "healthy",
  "service": "sparkjar-crews",
  "environment": "development",
  "available_crews": ["memory_maker_crew", "book_ingestion_crew"],
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Execute Crew
```
POST /execute_crew
Authorization: Bearer <jwt_token>
```
Execute a crew with provided inputs.

**Request:**
```json
{
  "crew_name": "memory_maker_crew",
  "inputs": {
    "text_content": "Sample text to analyze",
    "actor_type": "human",
    "actor_id": "user-123",
    "client_user_id": "client-456"
  },
  "timeout": 300
}
```

**Response:**
```json
{
  "success": true,
  "crew_name": "memory_maker_crew",
  "result": "Crew execution completed successfully",
  "error": null,
  "execution_time": 45.2,
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### List Crews
```
GET /crews
Authorization: Bearer <jwt_token>
```
List all available crews and their metadata.

**Response:**
```json
{
  "available_crews": {
    "memory_maker_crew": {
      "class_name": "MemoryMakerCrew",
      "module": "crews.memory_maker_crew.crew",
      "description": "Memory Maker Crew for conversation analysis"
    }
  },
  "total_count": 1,
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Authentication

All endpoints except `/health` require JWT authentication with appropriate scopes:

- **Required Scopes**: `sparkjar_internal` OR `crew_execute`
- **Token Format**: Bearer token in Authorization header
- **Token Validation**: Validates signature, expiration, and scopes

## Running the Service

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
python run_api.py
```

### Production
```bash
# Run with uvicorn
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

## Configuration

The service uses environment variables for configuration:

- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_SECRET_KEY`: JWT secret key
- `ENVIRONMENT`: Environment (development/staging/production)

## Logging

- **Development**: Human-readable console logging
- **Production**: Structured JSON logging with request tracing
- **Request IDs**: Each request gets a unique ID for tracing
- **Log Levels**: Configurable based on environment

## Error Handling

- **Validation Errors**: 422 for invalid request data
- **Authentication Errors**: 401 for invalid tokens, 403 for insufficient scopes
- **Not Found**: 404 for non-existent crews
- **Server Errors**: 500 for unexpected errors with proper logging

## Testing

```bash
# Run unit tests
pytest tests/test_api_server.py -v

# Run integration tests
python test_integration.py
```

## Monitoring

- Health check endpoint for service monitoring
- Request/response logging with timing
- Error tracking and alerting
- Distributed tracing support

## Security

- JWT token validation with scope checking
- CORS configuration based on environment
- Input validation and sanitization
- Secure error messages (no sensitive data exposure)