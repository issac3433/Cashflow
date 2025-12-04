# How to Run the App

## Prerequisites

### For iOS (iPhone/Xcode):
- Xcode installed
- iPhone connected via USB (for physical device)
- OR iOS Simulator available

### For Android (Android Studio):
- Android Studio installed
- Android SDK configured
- Android emulator running OR physical device connected

## Quick Start

### Run on iOS (iPhone):
```bash
cd cashflow/mobile
./run_ios.sh
```

Or manually:
```bash
cd cashflow/mobile
npx expo run:ios --device  # For physical iPhone
# OR
npx expo run:ios           # For iOS Simulator
```

### Run on Android:
```bash
cd cashflow/mobile
./run_android.sh
```

Or manually:
```bash
cd cashflow/mobile
npx expo run:android
```

## Using Xcode (iOS)

1. **Open the project:**
   ```bash
   cd cashflow/mobile
   npx expo prebuild --platform ios
   open ios/*.xcworkspace
   ```

2. **In Xcode:**
   - Select your iPhone from the device dropdown (top bar)
   - Select your development team (Signing & Capabilities)
   - Click the Play button (▶️) or press `Cmd + R`

## Using Android Studio

1. **Open the project:**
   ```bash
   cd cashflow/mobile
   npx expo prebuild --platform android
   ```
   Then open `cashflow/mobile/android` folder in Android Studio

2. **In Android Studio:**
   - Select your emulator/device from the device dropdown
   - Click the Run button (▶️) or press `Shift + F10`

## Backend Required

**IMPORTANT:** Make sure the backend is running before starting the app:

```bash
cd cashflow/backend
./start_backend.sh
```

Or manually:
```bash
cd cashflow/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### iOS Issues:
- **"No iOS devices available"**: Connect iPhone via USB and trust computer
- **"Developer disk image" error**: iPhone iOS version not supported by Xcode
- **Signing errors**: Select your development team in Xcode

### Android Issues:
- **"SDK location not found"**: Run `./run_android.sh` to auto-configure
- **"No devices"**: Start Android emulator or connect physical device
- **Build errors**: Make sure Android Studio SDK is properly installed

## Network Configuration

The app automatically uses:
- **Android Emulator**: `http://10.0.2.2:8000` (special IP for emulator → host)
- **iOS Simulator**: `http://localhost:8000`
- **Physical Devices**: `http://YOUR_MAC_IP:8000` (auto-detected)

Your Mac's IP is stored in `src/services/api.ts` and updates automatically.

