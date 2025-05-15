from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import json
from datetime import datetime
import logging

# Import routers from route modules
from routes import pending_routes, approved_routes, utils_routes
from routes.utils_routes import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger("policy_tracker_api")

# Create FastAPI application
app = FastAPI(
    title="Policy Tracker API",
    description="API for tracking and managing policy initiatives",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ideally, specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
ensure_directories()

# Include routers from different modules
app.include_router(pending_routes.router)
app.include_router(approved_routes.router)
app.include_router(utils_routes.router)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)