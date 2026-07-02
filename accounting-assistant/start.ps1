# Accounting Assistant - Автоматический запуск
# Просто запусти: .\start.ps1

# Завершить старые процессы
Write-Host "🔴 Завершаю старые процессы..." -ForegroundColor Red
Get-Process python, node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Переменные
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"
$frontendPath = Join-Path $scriptPath "frontend"

# Установить кодировку
$env:PYTHONIOENCODING = "utf-8"

# Запустить Backend в новом окне
Write-Host "🟢 Запускаю Backend..." -ForegroundColor Green
$backendCmd = "cd '$backendPath'; python simple_server.py; pause"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# Запустить Frontend в новом окне
Start-Sleep -Seconds 3
Write-Host "🟢 Запускаю Frontend..." -ForegroundColor Green
$frontendCmd = "cd '$frontendPath'; npm run dev -- --host 0.0.0.0; pause"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

# Ждём запуска
Start-Sleep -Seconds 5

# Открыть браузер
Write-Host "🌐 Открываю браузер..." -ForegroundColor Cyan
Start-Process "http://localhost:3030"

Write-Host "`n✅ Оба сервера запущены!" -ForegroundColor Green
Write-Host "📍 Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "📍 Frontend: http://localhost:3030" -ForegroundColor Cyan
Write-Host "🔑 Пароль:   123" -ForegroundColor Yellow
