# Cashflow - Investment Portfolio Management App

A mobile application for managing investment portfolios with real-time stock tracking, risk analysis, dividend forecasting, and biometric authentication.

## 📋 Summary

Cashflow is a full-stack investment portfolio management app built with React Native (Expo) and FastAPI. It allows users to track their stock portfolios, analyze risk, forecast dividend income, and manage cash balances across multiple portfolio types. The app features biometric authentication, real-time price updates, and comprehensive financial analytics.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Neon PostgreSQL account
- Supabase account (for authentication)

### Setup

**1. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env file with DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY
```

**2. Mobile App Setup**
```bash
cd mobile
npm install
# Create .env file with EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY
```

**3. Start the App**

For **home WiFi**:
```bash
./home.sh          # Terminal 1: Start backend
cd mobile && npx expo start  # Terminal 2: Start mobile app
```

For **school WiFi**:
```bash
./school.sh        # Terminal 1: Start backend
cd mobile && npx expo start  # Terminal 2: Start mobile app
```

**Note:** Update `mobile/src/services/api.ts` with your current IP address when switching networks.

## 🎯 Key Features

- **Portfolio Management** - Create and manage multiple portfolios (Individual & Retirement)
- **Stock Trading** - Buy and sell stocks with real-time price calculations
- **Risk Analysis** - Comprehensive risk assessment with volatility, beta, Sharpe ratio, and VaR
- **Dividend Forecasting** - Project future dividend income with multiple growth scenarios
- **Dividend Calendar** - View upcoming dividend payments organized by month
- **Biometric Auth** - FaceID/TouchID support for secure login
- **Cash Management** - Add/withdraw cash from portfolios

## 🛠️ Tech Stack

**Frontend:** React Native (Expo), TypeScript, React Navigation, Supabase Auth  
**Backend:** FastAPI, SQLModel, PostgreSQL (Neon), Polygon.io API  
**Infrastructure:** Neon PostgreSQL, Supabase (auth only)

## 📁 Project Structure

```
cashflow/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── routers/  # API endpoints
│   │   ├── services/ # Business logic
│   │   └── models.py # Database models
│   └── start_backend.sh
│
├── mobile/           # React Native app
│   ├── src/
│   │   ├── screens/  # App screens
│   │   ├── services/ # API & Supabase clients
│   │   └── navigation/
│   └── package.json
│
├── home.sh           # Start backend (home WiFi)
└── school.sh         # Start backend (school WiFi)
```

## 📱 Running the App

**iOS:**
```bash
cd mobile
npx expo run:ios
```

**Android:**
```bash
cd mobile
npx expo run:android
```

**Expo Go (Quick Testing):**
```bash
cd mobile
npx expo start
# Scan QR code with Expo Go app
```

## 🔧 Configuration

### Network Setup

The mobile app needs your Mac's IP address to connect to the backend:
- **Android Emulator:** Uses `http://10.0.2.2:8000` automatically
- **iOS Simulator:** Uses `http://localhost:8000` automatically  
- **Physical Devices:** Update IP in `mobile/src/services/api.ts`

Find your IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}'
```

### Environment Variables

**Backend (.env):**
```
DATABASE_URL=your_neon_postgresql_url
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
POLYGON_API_KEY=your_polygon_key (optional)
```

**Mobile (.env):**
```
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🐛 Troubleshooting

**Backend won't start:**
- Check virtual environment is activated
- Verify `.env` file exists with correct values
- Check port 8000 is available: `lsof -i :8000`

**Mobile app can't connect:**
- Ensure backend is running: `curl http://localhost:8000/health`
- Update IP address in `mobile/src/services/api.ts` for physical devices
- Ensure devices are on the same network

**FaceID not working:**
- Requires development build (`npx expo run:ios`) - doesn't work in Expo Go
- Check device has FaceID/TouchID enabled

## 📄 License

This project is part of a capstone project.

## 👤 Author

Nathaniel Issac
