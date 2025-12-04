#!/bin/bash

# Start both backend and mobile app
# This script starts the backend server and then the Expo dev server

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
MOBILE_DIR="$SCRIPT_DIR/mobile"

echo "🚀 Starting Cashflow Application..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $EXPO_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "📡 Starting backend server..."
cd "$BACKEND_DIR"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend may still be starting..."
fi

echo ""
echo "📱 Starting Expo dev server..."
echo ""

# Start Expo
cd "$MOBILE_DIR"
npx expo start &
EXPO_PID=$!

echo ""
echo "✅ Both servers are starting..."
echo "📡 Backend: http://localhost:8000"
echo "📱 Expo: Check terminal for QR code"
echo ""
echo "Press CTRL+C to stop both servers"
echo ""

# Wait for both processes
wait

