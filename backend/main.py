from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import routers from route modules
from routes import pending_routes, approved_routes, utils_routes
from routes.utils_routes import ensure_directories

# Create FastAPI application
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,                   
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
ensure_directories()

# Mount static directories for policy files
app.mount("/files", StaticFiles(directory="temp_policies"), name="temp_policy_files")
app.mount("/approved", StaticFiles(directory="approved_policies"), name="approved_policy_files")

# Include routers from different modules
app.include_router(pending_routes.router)
app.include_router(approved_routes.router)
app.include_router(utils_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)