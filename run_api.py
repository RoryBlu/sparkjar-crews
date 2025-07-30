#!/usr/bin/env python
"""
SparkJAR Crews API Server Startup Script

This script starts the FastAPI server for the crews service.
"""

import uvicorn
from sparkjar_shared.config.shared_settings import API_HOST, API_PORT, ENVIRONMENT

if __name__ == "__main__":
    print(f"🚀 Starting SparkJAR Crews API Server")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Server: http://{API_HOST}:{API_PORT}")
    print(f"Docs: http://{API_HOST}:{API_PORT}/docs")
    
    uvicorn.run(
        "api.server:app",
        host=API_HOST,
        port=API_PORT,
        reload=ENVIRONMENT == "development",
        log_level="info",
        access_log=True
    )