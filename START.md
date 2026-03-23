# CARVanta — How to Start

## Option 1: Double-click start script
Just double-click `start.bat` in the CARVanta folder. It starts both servers automatically.

## Option 2: Manual start

### Terminal 1: Backend (FastAPI)
```powershell
cd C:\Users\dhruv\CARVanta
C:\Users\dhruv\carvanta_env\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```
Wait for "Application startup complete" message.
Opens at: **http://localhost:8001**

### Terminal 2: Frontend (React + Vite)
```powershell
cd C:\Users\dhruv\CARVanta\frontend-react
npm run dev
```
Opens at: **http://localhost:5173**

## Important Notes
- **Always start the backend FIRST**, then the frontend
- Backend takes ~15 seconds to load (it precomputes 16,000 rankings)
- If you see "Request failed with status code 500" on login, the backend is not running yet

## Quick Health Check
Open in browser: **http://localhost:8001/health**
If you see JSON data, the backend is working.
