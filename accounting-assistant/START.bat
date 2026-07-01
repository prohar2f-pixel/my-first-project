@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title Accounting Assistant - Both Servers

echo ============================================
echo   ACCOUNTING ASSISTANT - STARTUP
echo ============================================
echo.

REM Kill existing processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [1/2] Запускаю BACKEND (http://localhost:8000)...
set PYTHONIOENCODING=utf-8
start "Backend - Accounting Assistant" /D "backend" python simple_server.py
timeout /t 3 /nobreak >nul

echo [2/2] Запускаю FRONTEND (http://localhost:3030)...
start "Frontend - Accounting Assistant" /D "frontend" cmd /k npm run dev

echo.
echo ============================================
echo ✅ Оба сервера запущены!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3030
echo.
echo Пароль: buhgalter2024
echo.
echo Открой браузер: http://localhost:3030
echo.
pause
