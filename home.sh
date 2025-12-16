#!/bin/bash

# Start backend for home WiFi
# Run this when you're at home, then start Expo separately with: npx expo start

cd "$(dirname "$0")/backend"

echo "🏠 Starting backend for home WiFi..."
echo "📍 Backend will be available at: http://0.0.0.0:8000"
echo "📱 Android emulator will connect via: http://10.0.2.2:8000"
echo "📱 Physical devices will use your Mac's IP (check ifconfig)"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
