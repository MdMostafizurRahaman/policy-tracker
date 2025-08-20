# Policy Tracker Environment Configuration

## Overview
All port numbers and URLs are now properly configured using environment variables from `.env` files, eliminating hardcoded values.

## Environment Files

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_NAME=Global Policy Tracker
NEXT_PUBLIC_APP_VERSION=4.0.0
NODE_ENV=development
NEXT_PUBLIC_ENABLE_GOOGLE_AUTH=false
PORT=3003
```

### Backend (.env)
```env
# Database Configuration
DATABASE_NAME="ai_policy_database"

# API Keys
OPENAI_API_KEY="sk-proj-..."
GROQ_API_KEY="gsk_..."

# Frontend Configuration  
FRONTEND_URL="http://localhost:3003"
BACKEND_PORT=8000
BACKEND_HOST="0.0.0.0"

# CORS Configuration
ALLOWED_ORIGINS="...,http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,..."

# Additional configuration...
```

## Port Configuration

### Current Setup
- **Frontend**: Port 3003 (configurable via `PORT` in .env.local)
- **Backend**: Port 8000 (configurable via `BACKEND_PORT` in .env)

### Environment Variable Hierarchy
1. **Frontend Port**: `PORT` → defaults to Next.js auto-assignment
2. **Backend Port**: `BACKEND_PORT` → `PORT` → 8000
3. **Backend Host**: `BACKEND_HOST` → "0.0.0.0"
4. **API URL**: `NEXT_PUBLIC_API_URL` → "http://localhost:8000/api"

## Code Changes Made

### 1. Frontend Configuration (`src/config/config.js`)
```javascript
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  // ... other config
};
```

### 2. Backend Configuration (`main.py`)
```python
if __name__ == "__main__":
    import os
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    port = int(os.environ.get("BACKEND_PORT", os.environ.get("PORT", 8000)))
    uvicorn.run("main:app", host=host, port=port, reload=True)
```

### 3. CORS Configuration
- Updated `ALLOWED_ORIGINS` to include ports 3000-3003
- Both localhost and 127.0.0.1 variants supported

## Development Scripts

### Quick Start
```bash
# Frontend
cd frontend
npm run dev

# Backend  
cd backend
python main.py
```

### Environment-Aware Start
```bash
# Use the provided startup scripts
./start-dev.sh        # Linux/Mac
./start-dev.ps1       # Windows PowerShell
python start-backend.py  # Backend only
```

## How to Change Ports

### Option 1: Environment Variables
```bash
# Frontend
export PORT=3005
npm run dev

# Backend
export BACKEND_PORT=8001
export BACKEND_HOST=127.0.0.1
python main.py
```

### Option 2: Update .env Files
```env
# frontend/.env.local
PORT=3005

# backend/.env
BACKEND_PORT=8001
BACKEND_HOST=127.0.0.1
FRONTEND_URL="http://localhost:3005"
```

### Option 3: Runtime Override
```bash
# Frontend
PORT=3005 npm run dev

# Backend
BACKEND_PORT=8001 python main.py
```

## Key Benefits

✅ **No Hardcoded Ports** - All ports configurable via environment  
✅ **Development Flexibility** - Easy to change ports for different setups  
✅ **Production Ready** - Same configuration system works in production  
✅ **CORS Properly Configured** - All common development ports included  
✅ **Environment Isolation** - Different environments can use different ports  

## Troubleshooting

### Port Conflicts
If you get "port in use" errors:
1. Check what's using the port: `netstat -an | findstr :3003`
2. Change the port in the appropriate .env file
3. Update CORS origins if needed

### API Connection Issues
1. Verify `NEXT_PUBLIC_API_URL` in frontend/.env.local
2. Check `ALLOWED_ORIGINS` includes your frontend URL
3. Ensure backend is running and accessible

### Environment Loading
- Frontend: Uses Next.js automatic .env.local loading
- Backend: Manual loading in main.py and startup scripts
- Verify environment files exist and have correct syntax
