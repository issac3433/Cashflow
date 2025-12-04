#!/bin/bash

# Backend startup script for Cashflow
# This script ensures the backend is always running

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Check if backend is already running
if lsof -i :8000 | grep -q LISTEN; then
    echo "✅ Backend is already running on port 8000"
    exit 0
fi

echo "🚀 Starting Cashflow backend server..."
echo "📍 Backend will be available at: http://0.0.0.0:8000"
echo "📱 For Android emulator: http://10.0.2.2:8000"
echo "📱 For iOS simulator/physical device: http://$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}'):8000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

