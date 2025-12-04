# Backend Startup Guide

## Quick Start

To start the backend server:

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

## Check if Backend is Running

```bash
# Check if port 8000 is in use
lsof -i :8000

# Test the health endpoint
curl http://localhost:8000/health
```

## Backend URLs

- **Localhost**: http://localhost:8000
- **Android Emulator**: http://10.0.2.2:8000
- **iOS Simulator/Physical Device**: http://YOUR_MAC_IP:8000

To find your Mac's IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## Keep Backend Running

The backend will run until you:
- Press `CTRL+C` in the terminal
- Close the terminal window
- Restart your computer

For production, consider using:
- `screen` or `tmux` to keep it running in background
- `pm2` or `supervisor` for process management
- System service (systemd on Linux, launchd on macOS)

## Troubleshooting

**Port already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Backend not responding:**
1. Check if it's running: `lsof -i :8000`
2. Check logs for errors
3. Restart: `./start_backend.sh`

