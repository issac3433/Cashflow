# Cashflow - Investment Portfolio Management App

A comprehensive mobile application for managing investment portfolios with real-time stock tracking, risk analysis, dividend forecasting, and biometric authentication.

## 🚀 Features

### Core Features
- 🔐 **Biometric Authentication** - FaceID/TouchID support for secure, fast login
- 📊 **Portfolio Management** - Create and manage multiple portfolios (Individual & Retirement)
- 💰 **Stock Trading** - Buy and sell stocks with real-time price calculations
- 💵 **Cash Management** - Add/withdraw cash from portfolios with instant balance updates
- 📈 **Real-time Price Updates** - Live stock prices from Polygon.io API
- 📱 **Cross-platform** - Native iOS and Android support via React Native/Expo

### Advanced Features
- 🎯 **Risk Analysis** - Comprehensive risk assessment with 0-100 risk scores, volatility, beta, Sharpe ratio, VaR, and concentration analysis
- 🔮 **Income Forecasting** - Project future dividend income with multiple growth scenarios
- 📅 **Dividend Calendar** - View all upcoming dividend payments organized by month
- 📊 **Performance Tracking** - Track total net worth, portfolio values, and lifetime dividend income
- ⚡ **Optimized Performance** - Instant home screen loading with optimized API calls

## 🛠️ Tech Stack

### Frontend (Mobile)
- **React Native** with **Expo** - Cross-platform mobile development
- **TypeScript** - Type-safe development
- **React Navigation** - Stack and Tab navigation
- **Supabase** - Authentication and user management
- **Axios** - HTTP client for API calls
- **Expo Local Authentication** - FaceID/TouchID integration
- **AsyncStorage** - Local credential storage

### Backend
- **FastAPI** - Modern Python web framework
- **SQLModel** - Database ORM with SQLite/PostgreSQL support
- **Supabase** - Authentication integration
- **Polygon.io API** - Real-time stock prices and market data
- **yfinance** - Financial data fetching
- **Pandas & NumPy** - Data analysis and calculations

### Infrastructure
- **SQLite** - Local database (development)
- **PostgreSQL** - Production database (via Supabase)
- **Redis** - Caching and task queue (optional)
- **Celery** - Background task processing (optional)

## 📁 Project Structure

```
Capstone/
├── cashflow/
│   ├── backend/              # FastAPI backend
│   │   ├── app/
│   │   │   ├── routers/      # API endpoints
│   │   │   ├── services/     # Business logic
│   │   │   ├── models.py     # Database models
│   │   │   └── main.py       # FastAPI app
│   │   ├── requirements.txt
│   │   ├── start_backend.sh  # Backend startup script
│   │   └── README_START.md
│   │
│   ├── mobile/               # React Native mobile app
│   │   ├── src/
│   │   │   ├── screens/      # App screens
│   │   │   ├── context/      # React Context (Auth)
│   │   │   ├── navigation/   # Navigation setup
│   │   │   ├── services/     # API & Supabase clients
│   │   │   └── theme/       # UI theme (colors, typography)
│   │   ├── run_android.sh    # Android build script
│   │   ├── run_ios.sh        # iOS build script
│   │   └── README.md
│   │
│   └── start_all.sh          # Start both backend + mobile
│
├── README.md                 # This file
├── README_START.md           # Quick start guide
└── PRESENTATION_SCREENS.md   # Screen descriptions for presentation
```

## 🏃 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- iOS: Xcode (for iOS development)
- Android: Android Studio (for Android development)
- Supabase account (for authentication)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Capstone/cashflow
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create .env file with:
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_key
# POLYGON_API_KEY=your_polygon_api_key (optional)
# ALPHAVANTAGE_API_KEY=your_alpha_key (optional)
```

### 3. Mobile App Setup

```bash
cd mobile

# Install dependencies
npm install

# Configure environment variables
# Create .env file with:
# EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
# EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
# EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4. Start Everything

**Option 1: Start both at once**
```bash
cd cashflow
./start_all.sh
```

**Option 2: Start separately**

Terminal 1 - Backend:
```bash
cd cashflow/backend
./start_backend.sh
```

Terminal 2 - Mobile:
```bash
cd cashflow/mobile
npx expo start
```

## 📱 Running the App

### iOS
```bash
cd cashflow/mobile
./run_ios.sh
# Or manually:
npx expo run:ios
```

### Android
```bash
cd cashflow/mobile
./run_android.sh
# Or manually:
npx expo run:android
```

### Expo Go (Quick Testing)
```bash
cd cashflow/mobile
npx expo start
# Scan QR code with Expo Go app
```

## 🎯 App Screens

### 1. Login Screen
Secure authentication with FaceID/TouchID biometric support. Users can sign up or sign in, with automatic biometric setup prompt after successful authentication.

### 2. Home Screen
Dashboard showing total net worth, portfolio value, cash balance, and total dividends. Create new portfolios and view all portfolios with quick navigation.

### 3. Portfolio Screen
Detailed view of holdings with real-time prices. Buy/sell stocks with live cost calculations and validation. Shows portfolio performance metrics.

### 4. Risk Analysis Screen
Comprehensive risk assessment with 0-100 risk scores, volatility, beta, Sharpe ratio, VaR, and concentration analysis. Two modes: Quick Overview and Comprehensive.

### 5. Forecast Screen
Project future dividend income with multiple growth scenarios (conservative, moderate, optimistic, pessimistic). Includes dividend reinvestment and recurring deposits.

### 6. Dividends Screen
Calendar view of all upcoming dividend payments organized by month. Shows ex-dates, payment dates, and total income per holding.

### 7. Profile Screen
Account management with cash add/withdraw functionality. Shows lifetime dividend income and account summary.

*See `PRESENTATION_SCREENS.md` for detailed screen descriptions.*

## 🔌 API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /auth/debug` - Debug authentication

### Profile
- `GET /profile` - Get user profile and portfolio summary
- `POST /profile/cash/add` - Add cash to portfolio
- `POST /profile/cash/withdraw` - Withdraw cash from portfolio

### Portfolios
- `GET /portfolios` - List all portfolios
- `POST /portfolios` - Create new portfolio
- `GET /portfolios/{id}` - Get portfolio details with holdings

### Holdings
- `POST /holdings` - Buy stock (create holding)
- `POST /holdings/{id}/sell` - Sell stock (partial or full)

### Risk Analysis
- `GET /risk/metrics/{portfolio_id}` - Quick risk overview
- `GET /risk/analysis/{portfolio_id}` - Comprehensive risk analysis

### Forecasts
- `POST /forecasts/monthly` - Generate monthly income forecast

### Dividends
- `GET /dividends/calendar` - Get dividend calendar
- `POST /dividends/process` - Process dividend payments

## 🔧 Configuration

### Network Configuration

The mobile app automatically detects the platform and uses the appropriate API URL:
- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS Simulator**: `http://localhost:8000`
- **Physical Devices**: `http://YOUR_MAC_IP:8000`

Update `mobile/src/services/api.ts` with your Mac's IP address for physical device testing.

### Environment Variables

**Backend (.env)**
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
POLYGON_API_KEY=your_polygon_key (optional)
ALPHAVANTAGE_API_KEY=your_alpha_key (optional)
```

**Mobile (.env)**
```
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**
```bash
lsof -i :8000
lsof -ti:8000 | xargs kill -9
```

**Backend not starting:**
- Check virtual environment is activated
- Verify all dependencies are installed
- Check `.env` file exists with correct values

### Mobile App Issues

**Can't connect to backend:**
- Ensure backend is running: `curl http://localhost:8000/health`
- For physical devices: Update API_BASE_URL with your Mac's IP
- Check firewall settings
- Ensure devices are on same network

**FaceID not working:**
- FaceID requires a development build (`npx expo run:ios`) - doesn't work in Expo Go
- Ensure `NSFaceIDUsageDescription` is set in `app.json`
- Check device has FaceID/TouchID enabled

**Build errors:**
- Clear cache: `npx expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- For Android: Ensure `ANDROID_HOME` is set and `local.properties` exists

### Android Build Issues

**SDK location not found:**
```bash
cd cashflow/mobile/android
echo "sdk.dir=$HOME/Library/Android/sdk" > local.properties
```

**Use the provided script:**
```bash
cd cashflow/mobile
./run_android.sh
```

## 📊 Performance Optimizations

- **Home Screen**: Uses stored average prices instead of real-time fetching for instant loading
- **Price Fetching**: Parallel API calls with timeout protection (2s max)
- **Database Queries**: Batched queries to eliminate N+1 problems
- **Dividend Queries**: Single batch query instead of per-holding queries
- **Caching**: Price caching with 2-minute TTL to reduce API calls

## 🔒 Security Features

- **Biometric Authentication**: Device-level security with FaceID/TouchID
- **Secure Storage**: Credentials stored in device keychain/keystore
- **JWT Tokens**: Secure authentication tokens via Supabase
- **Input Validation**: Client and server-side validation
- **Error Handling**: Graceful error handling without exposing sensitive data

## 📝 Development Notes

- The app uses React Navigation for screen navigation
- AsyncStorage is used for token persistence
- Axios interceptors automatically add auth tokens to requests
- TypeScript provides type safety throughout
- Expo provides hot reloading for fast development

## 🚀 Deployment

### Backend
- Deploy FastAPI app to cloud provider (Heroku, Railway, AWS, etc.)
- Update `EXPO_PUBLIC_API_BASE_URL` in mobile app
- Configure CORS for your mobile app domain

### Mobile App
- Build for production: `npx expo build:ios` or `npx expo build:android`
- Or use EAS Build: `eas build --platform ios/android`
- Submit to App Store / Google Play Store

## 📄 License

This project is part of a capstone project.

## 👤 Author

Nathaniel Issac

## 🙏 Acknowledgments

- Supabase for authentication infrastructure
- Polygon.io for market data
- Expo team for React Native tooling
- FastAPI for the excellent Python framework

