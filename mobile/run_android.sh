#!/bin/bash

# Android Build and Run Script
# This script builds and runs the app on Android Studio emulator

cd "$(dirname "$0")"

echo "🤖 Building and running Android app..."
echo ""

# Set ANDROID_HOME environment variable
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools:$PATH"

echo "📱 Android SDK: $ANDROID_HOME"

# Check if Android SDK is configured
if [ ! -f "android/local.properties" ]; then
    echo "⚠️  Android SDK location not configured"
    echo "Creating local.properties..."
    echo "sdk.dir=$ANDROID_HOME" > android/local.properties
else
    # Ensure local.properties has correct path
    if ! grep -q "sdk.dir=$ANDROID_HOME" android/local.properties 2>/dev/null; then
        echo "sdk.dir=$ANDROID_HOME" >> android/local.properties
    fi
fi

# Verify SDK exists
if [ ! -d "$ANDROID_HOME" ]; then
    echo "❌ Android SDK not found at $ANDROID_HOME"
    echo "Please install Android Studio or set ANDROID_HOME manually"
    exit 1
fi

echo "✅ Android SDK configured"
echo ""

# Build and run
npx expo run:android

