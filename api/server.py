"""
SparkJAR Crews Service API Server

This FastAPI server provides HTTP endpoints for executing crews remotely.
It handles crew execution requests from the API gateway and returns structured results.
"""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# Import shared components
from sparkjar_shared.auth import verify_token, InvalidTokenError
from sparkjar_shared.config.shared_settings import ENVIRONMENT, API_HOST, API_PORT
from sparkjar_shared.schemas import (
    CrewExecutionRequest,
    CrewExecutionResponse,
    CrewHealthResponse,
    CrewListResponse
)

# Import crew registry
from .crew_registry import CREW_REGISTRY
from .logging_config import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger(__name__)

# Security
security = HTTPBearer()

# Request tracing middleware
class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request tracing and logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        start_time = datetime.utcnow()
        
        try:
            response = await call_next(request)
            
            # Log request completion
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log request error
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration
                }
            )
            raise

# FastAPI app
app = FastAPI(
    title="SparkJAR Crews Service",
    description="HTTP API for executing CrewAI crews remotely",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
)

# Add middleware
app.add_middleware(RequestTracingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Request/Response Models are imported from shared schemas

# Authentication dependency
async def verify_internal_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token for internal service authentication.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or missing required scopes
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        # Check for required scopes
        scopes = payload.get("scopes", [])
        if "sparkjar_internal" not in scopes and "crew_execute" not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Required scope: sparkjar_internal or crew_execute"
            )
        
        return payload
        
    except InvalidTokenError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API Endpoints
@app.get("/health", response_model=CrewHealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and service discovery.
    
    Returns:
        Service health status and available crews
    """
    return CrewHealthResponse(
        status="healthy",
        service="sparkjar-crews",
        environment=ENVIRONMENT,
        available_crews=list(CREW_REGISTRY.keys())
    )

@app.post("/execute_crew", response_model=CrewExecutionResponse)
async def execute_crew(
    crew_request: CrewExecutionRequest,
    request: Request,
    token_payload: Dict[str, Any] = Depends(verify_internal_token)
) -> CrewExecutionResponse:
    """
    Execute a crew with the provided inputs.
    
    Args:
        crew_request: Crew execution request containing crew name and inputs
        request: FastAPI request object for tracing
        token_payload: Verified JWT token payload
        
    Returns:
        Crew execution response with results or error information
    """
    start_time = datetime.utcnow()
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    try:
        # Validate crew exists
        if crew_request.crew_name not in CREW_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crew '{crew_request.crew_name}' not found. Available crews: {list(CREW_REGISTRY.keys())}"
            )
        
        # Log execution start
        logger.info(
            f"Starting execution of crew '{crew_request.crew_name}' for user {token_payload.get('sub')}",
            extra={
                "request_id": request_id,
                "crew_name": crew_request.crew_name,
                "user_id": token_payload.get('sub')
            }
        )
        logger.debug(f"Crew inputs: {crew_request.inputs}")
        
        # Get crew handler class and instantiate
        handler_class = CREW_REGISTRY[crew_request.crew_name]
        
        # Create handler instance
        crew_handler = handler_class()
        
        # Execute the crew using the handler
        result = await crew_handler.execute(crew_request.inputs)
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"Crew '{crew_request.crew_name}' executed successfully in {execution_time:.2f}s",
            extra={
                "request_id": request_id,
                "crew_name": crew_request.crew_name,
                "execution_time": execution_time
            }
        )
        
        # Check if handler returned success
        if isinstance(result, dict) and result.get("status") == "completed":
            return CrewExecutionResponse(
                success=True,
                crew_name=crew_request.crew_name,
                result=result,
                execution_time=execution_time
            )
        else:
            # Handle failure from handler
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
            return CrewExecutionResponse(
                success=False,
                crew_name=crew_request.crew_name,
                error=error_msg,
                result=result,
                execution_time=execution_time
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_msg = f"Crew execution failed: {str(e)}"
        
        logger.error(
            f"Error executing crew '{crew_request.crew_name}': {error_msg}",
            extra={
                "request_id": request_id,
                "crew_name": crew_request.crew_name,
                "execution_time": execution_time,
                "error": error_msg
            }
        )
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return CrewExecutionResponse(
            success=False,
            crew_name=crew_request.crew_name,
            error=error_msg,
            execution_time=execution_time
        )

@app.get("/crews", response_model=CrewListResponse)
async def list_crews(
    token_payload: Dict[str, Any] = Depends(verify_internal_token)
) -> Dict[str, Any]:
    """
    List all available crews and their information.
    
    Args:
        token_payload: Verified JWT token payload
        
    Returns:
        Dictionary of available crews and their metadata
    """
    crews_info = {}
    
    for crew_name, crew_class in CREW_REGISTRY.items():
        try:
            # Get basic crew information
            crews_info[crew_name] = {
                "class_name": crew_class.__name__,
                "module": crew_class.__module__,
                "description": crew_class.__doc__ or "No description available"
            }
        except Exception as e:
            crews_info[crew_name] = {
                "error": f"Failed to get crew info: {str(e)}"
            }
    
    return CrewListResponse(
        available_crews=crews_info,
        total_count=len(CREW_REGISTRY),
        timestamp=datetime.utcnow()
    )

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error occurred"
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info(f"🚀 SparkJAR Crews Service starting up")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Available crews: {list(CREW_REGISTRY.keys())}")
    logger.info(f"Server will run on {API_HOST}:{API_PORT}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 SparkJAR Crews Service shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host=API_HOST,
        port=API_PORT,
        reload=ENVIRONMENT == "development",
        log_level="info"
    )