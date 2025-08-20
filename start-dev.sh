#!/bin/bash
# Development startup script for Policy Tracker

echo "🚀 Starting Policy Tracker Development Environment"
echo "=================================================="

# Load environment variables
export $(cat .env | grep -v ^# | xargs)

# Get configuration from environment
BACKEND_HOST=${BACKEND_HOST:-"0.0.0.0"}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${PORT:-3003}

echo "📊 Configuration:"
echo "  Backend: http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend: http://localhost:${FRONTEND_PORT}"
echo "  API URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000/api}"
echo ""

# Start backend
echo "🔧 Starting Backend Server..."
cd backend
python main.py &
BACKEND_PID=$!

# Start frontend
echo "🌐 Starting Frontend Server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers started!"
echo "📊 Backend PID: $BACKEND_PID"
echo "🌐 Frontend PID: $FRONTEND_PID"
echo ""
echo "🌍 Open http://localhost:${FRONTEND_PORT} in your browser"
echo ""
echo "💡 To stop both servers, run: kill $BACKEND_PID $FRONTEND_PID"

# Wait for both processes
wait
