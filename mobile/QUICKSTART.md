# Quick Start Guide

## 1. Install Dependencies
```bash
cd mobile
npm install
```

## 2. Configure Environment

Create a `.env` file in the `mobile` directory:
```bash
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

**For iPhone/Physical Device Testing:**
- Replace `localhost` with your Mac's IP address (e.g., `http://192.168.1.100:8000`)
- Make sure your backend is running with `--host 0.0.0.0`

## 3. Start Backend
```bash
cd ../backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 4. Run Mobile App

**iOS Simulator:**
```bash
cd mobile
npm run ios
```

**Android Emulator:**
```bash
cd mobile
npm run android
```

**Physical Device (Expo Go):**
```bash
cd mobile
npm start
# Scan QR code with Expo Go app
```

## Features Implemented

✅ **Authentication**
- Sign up / Sign in with Supabase
- Automatic token management
- Session persistence

✅ **Home Screen**
- Total net worth display
- Portfolio summary cards
- Quick navigation to portfolios

✅ **Portfolio Screen**
- View all holdings
- Add new holdings (buy stocks)
- Sell holdings (partial or full)
- Real-time price updates
- Cash balance display

✅ **Profile Screen**
- Portfolio cash management
- Add/withdraw cash per portfolio
- Sign out functionality

## API Endpoints Used

- `GET /profile` - User profile and portfolio summary
- `GET /portfolios/{id}` - Portfolio details with holdings
- `POST /holdings` - Create new holding (buy stock)
- `POST /holdings/{id}/sell` - Sell holding
- `POST /profile/cash/add` - Add cash to portfolio
- `POST /profile/cash/withdraw` - Withdraw cash from portfolio
- `POST /me/init-supabase` - Initialize user in backend

## Troubleshooting

**"Network Error" or "Can't connect to API":**
- Check backend is running: `lsof -i :8000`
- For physical device: Update API_BASE_URL in `.env` to use your Mac's IP
- Ensure phone and computer are on same WiFi network

**"Supabase not configured":**
- Check `.env` file has correct Supabase credentials
- Restart Expo: `npm start -c` (clears cache)

**Build errors:**
- Clear cache: `npx expo start -c`
- Reinstall: `rm -rf node_modules && npm install`

