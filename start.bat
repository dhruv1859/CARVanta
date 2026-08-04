@echo off
title CARVanta Server Startup
echo ============================================
echo   CARVanta - Starting Servers...
echo ============================================
echo.

:: Get the directory of this batch file
set "PROJECT_DIR=%~dp0"

:: Start backend in a new window using the virtual environment if exists, else global python
echo [1/2] Starting Backend (port 8001)...
if exist "%PROJECT_DIR%venv\Scripts\python.exe" (
    start "CARVanta Backend" cmd /k "cd /d %PROJECT_DIR% && venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8001"
) else (
    start "CARVanta Backend" cmd /k "cd /d %PROJECT_DIR% && python -m uvicorn api.main:app --host 0.0.0.0 --port 8001"
)

:: Wait for backend to initialize
echo      Waiting for backend to load...
timeout /t 10 /nobreak > nul

:: Start frontend in a new window
echo [2/2] Starting Frontend (port 5173)...
start "CARVanta Frontend" cmd /k "cd /d %PROJECT_DIR%frontend-react && npm run dev"

echo.
echo ============================================
echo   Both servers starting!
echo   Backend:  http://localhost:8001
echo   Frontend: http://localhost:5173
echo ============================================
echo.
echo Wait ~15 seconds for backend to finish loading,
echo then open http://localhost:5173 in your browser.
echo.
pause
