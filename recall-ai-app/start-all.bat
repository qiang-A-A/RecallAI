@echo off
title Recall AI Launcher
cd /d "%~dp0"

echo ============================================
echo   Recall AI - One-Click Launcher
echo   Frontend :5173  +  Backend :8000
echo ============================================
echo.

REM ----------------------------------------------------------------
REM Pre-check: ports must be free, otherwise stop and ask user to
REM close the existing backend/frontend windows first.
REM Only LISTENING state counts as "occupied"; SYN_SENT / TIME_WAIT
REM from browsers/WorkBuddy preview are ignored.
REM ----------------------------------------------------------------
netstat -ano | findstr "LISTENING" | findstr /C:":8000" >nul
if not errorlevel 1 (
  echo [WARN] Port 8000 is already in use.
  echo        A previous backend may still be running.
  echo        Please close the existing "Recall-Backend" window first.
  echo.
  pause
  exit /b 1
)
netstat -ano | findstr "LISTENING" | findstr /C:":5173" >nul
if not errorlevel 1 (
  echo [WARN] Port 5173 is already in use.
  echo        A previous frontend may still be running.
  echo        Please close the existing "Recall-Frontend" window first.
  echo.
  pause
  exit /b 1
)

REM ----------------------------------------------------------------
REM WorkBuddy-managed Node is not on the system PATH by default.
REM Locate npm via relative path and prepend it to PATH so the new
REM cmd window inherits it.
REM ----------------------------------------------------------------
set NPM_DIR=%~dp0..\..\..\.workbuddy\binaries\node\versions\22.22.2
set PATH=%NPM_DIR%;%PATH%
if not exist "%NPM_DIR%\npm.cmd" (
  echo [ERROR] Could not find npm at: %NPM_DIR%\npm.cmd
  echo         Please install Node.js or update the path in this script.
  pause
  exit /b 1
)

echo [1/2] Starting backend FastAPI (port 8000)...
start "Recall-Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo [2/2] Starting frontend Vite (port 5173)...
start "Recall-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Done! Two black windows should have opened.
echo Wait for the frontend window to show:
echo   Local: http://localhost:5173/
echo.
echo Then open in browser:  http://localhost:5173
echo Backend API docs:       http://127.0.0.1:8000/docs
echo.
echo To stop: close the two black windows.
pause
