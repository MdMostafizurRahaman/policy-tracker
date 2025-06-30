#!/bin/bash

# Development startup script for AI Policy Tracker

echo "🚀 Starting AI Policy Tracker Development Environment"
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Start backend in background
echo "🔧 Starting Backend (FastAPI)..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install backend dependencies if needed
if [ ! -f "app/requirements.txt" ] || [ ! -d "venv/lib" ]; then
    echo "📦 Installing Backend dependencies..."
    cd app
    pip install -r requirements.txt
    cd ..
fi

# Start backend
echo "🔧 Starting backend server on port 8000..."
python run.py &
BACKEND_PID=$!

cd ..

# Start frontend
echo "🔧 Starting Frontend (Next.js)..."
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Frontend dependencies..."
    npm install
fi

# Start frontend
echo "🔧 Starting frontend server on port 3000..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Development servers started!"
echo "🔗 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped. Goodbye!"
    exit 0
}

# Set trap to catch Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
