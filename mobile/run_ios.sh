#!/bin/bash

# iOS Build and Run Script
# This script builds and runs the app on iOS (iPhone or Simulator)

cd "$(dirname "$0")"

echo "🍎 Building and running iOS app..."
echo ""

# Check if device is connected
DEVICE=$(xcrun xctrace list devices 2>/dev/null | grep -i iphone | grep -v "Simulator" | head -1)

if [ -z "$DEVICE" ]; then
    echo "📱 No physical iPhone detected, using iOS Simulator..."
    npx expo run:ios
else
    echo "📱 iPhone detected: $DEVICE"
    echo "🔨 Building for device..."
    npx expo run:ios --device
fi

