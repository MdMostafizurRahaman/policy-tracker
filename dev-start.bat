@echo off
REM Development startup script for AI Policy Tracker (Windows)

echo 🚀 Starting AI Policy Tracker Development Environment
echo ==================================================

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM Start backend
echo 🔧 Starting Backend (FastAPI)...
cd backend

if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install backend dependencies if needed
if not exist "app\requirements.txt" goto skip_backend_install
if not exist "venv\Lib" (
    echo 📦 Installing Backend dependencies...
    cd app
    pip install -r requirements.txt
    cd ..
)
:skip_backend_install

REM Start backend in new window
echo 🔧 Starting backend server on port 8000...
start "Backend Server" cmd /k "python run.py"

cd ..

REM Start frontend
echo 🔧 Starting Frontend (Next.js)...
cd frontend

REM Install frontend dependencies if needed
if not exist "node_modules" (
    echo 📦 Installing Frontend dependencies...
    npm install
)

REM Start frontend in new window
echo 🔧 Starting frontend server on port 3000...
start "Frontend Server" cmd /k "npm run dev"

cd ..

echo.
echo ✅ Development servers started!
echo 🔗 Frontend: http://localhost:3000
echo 🔗 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause >nul
