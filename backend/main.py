"""
Main entry point for the AI Policy Tracker API.
This is the new structured version - the old main.py is preserved as main_old.py
"""
import uvicorn
from app_main import app

if __name__ == "__main__":
    uvicorn.run(
        "app_main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True, 
        log_level="info"
    )
