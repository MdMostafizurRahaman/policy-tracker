# Policy Tracker Backend

A FastAPI-based backend service for the Policy Tracker application.

## Features

- RESTful API for policy management
- File upload and storage with AWS S3
- User authentication and authorization
- Admin panel for policy management
- Real-time data processing
- DynamoDB integration for scalable data storage

## Installation

1. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the application:
   ```bash
   poetry run uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once the server is running, you can access:
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Deployment

This application is designed to be deployed on Render.com or similar platforms.
