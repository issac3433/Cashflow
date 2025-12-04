# Cashflow Mobile App

React Native mobile app built with Expo for managing your investment portfolio.

## Features

- 🔐 Supabase Authentication
- 📊 Portfolio Management
- 💰 Stock Holdings (Buy/Sell)
- 💵 Cash Management
- 📈 Real-time Price Updates
- 📱 Native iOS & Android Support

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Environment Variables**
   
   Copy `.env.example` to `.env` and fill in your Supabase credentials:
   ```bash
   cp .env.example .env
   ```
   
   Update `.env` with your values:
   ```
   EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   EXPO_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   ```

3. **Update API Base URL** (if needed)
   
   For development, the app defaults to `http://localhost:8000`. 
   
   For physical device testing, update `src/services/api.ts` to use your computer's IP address:
   ```typescript
   const API_BASE_URL = __DEV__ 
     ? 'http://YOUR_IP_ADDRESS:8000'  // e.g., 'http://192.168.1.100:8000'
     : 'https://your-api-domain.com';
   ```

4. **Start the Backend**
   
   Make sure your FastAPI backend is running on port 8000:
   ```bash
   cd ../backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Run the Mobile App**
   
   ```bash
   # iOS
   npm run ios
   
   # Android
   npm run android
   
   # Web (for testing)
   npm run web
   ```

## Project Structure

```
mobile/
├── src/
│   ├── context/          # React Context (Auth)
│   ├── navigation/       # Navigation setup
│   ├── screens/          # App screens
│   │   ├── LoginScreen.tsx
│   │   ├── HomeScreen.tsx
│   │   ├── PortfolioScreen.tsx
│   │   └── ProfileScreen.tsx
│   └── services/         # API & Supabase clients
│       ├── api.ts
│       └── supabase.ts
├── App.tsx               # Main app entry point
└── package.json
```

## API Integration

The app connects to your FastAPI backend at the endpoints:
- `/profile` - User profile and portfolio summary
- `/portfolios/{id}` - Portfolio details with holdings
- `/holdings` - Create new holdings (buy stocks)
- `/holdings/{id}/sell` - Sell holdings
- `/profile/cash/add` - Add cash to portfolio
- `/profile/cash/withdraw` - Withdraw cash from portfolio

## Authentication

The app uses Supabase for authentication. Users sign up/sign in through Supabase, and the JWT token is automatically sent to the backend API for authorization.

## Development Notes

- The app uses React Navigation for navigation
- AsyncStorage is used for token persistence
- Axios is used for API calls with automatic token injection
- TypeScript is used throughout for type safety

## Troubleshooting

**Can't connect to backend on physical device:**
- Make sure your backend is running with `--host 0.0.0.0`
- Update the API_BASE_URL in `src/services/api.ts` to use your computer's IP address
- Ensure your phone and computer are on the same network
- Check firewall settings

**Supabase connection issues:**
- Verify your `.env` file has the correct Supabase URL and anon key
- Make sure Supabase is properly configured in your backend

**Build errors:**
- Clear cache: `npx expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`

