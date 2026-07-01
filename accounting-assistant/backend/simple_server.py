#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой HTTP сервер для ассистента бухгалтера
Работает без внешних зависимостей (только встроенные модули Python)
"""

import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import sys
from datetime import datetime
import io

# Установить UTF-8 кодировку
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Загрузить .env файл
def load_env():
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value.strip()

load_env()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SECRET_PASSWORD = "123"  # Жестко установлен для тестирования

if not OPENROUTER_API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY не найден в .env файле!")
    sys.exit(1)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class RequestHandler(BaseHTTPRequestHandler):
    def send_json_response(self, status_code, data):
        """Вспомогательный метод для отправки JSON с CORS"""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        """Обработка GET запросов"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/api/health":
            self.send_json_response(200, {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0-simple"
            })

        elif parsed_path.path == "/api/tax-rates":
            self.send_json_response(200, {
                "ндфл": 13.0,
                "ес_взнос_пенс": 22.0,
                "ес_взнос_мед": 5.1,
                "ес_взнос_соц": 2.9,
                "ес_взнос_безопасность": 0.3
            })
        else:
            self.send_json_response(404, {"error": "Not found"})

    def do_POST(self):
        """Обработка POST запросов"""
        print(f"[POST] {self.path}")  # DEBUG
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
            print(f"[DATA] {data}")  # DEBUG
        except:
            data = {}

        parsed_path = urlparse(self.path)

        if parsed_path.path == "/api/auth":
            password = data.get("password", "")
            print(f"[AUTH] Пароль: {password}, Ожидаемо: {SECRET_PASSWORD}, Совпадение: {password == SECRET_PASSWORD}")
            if password == SECRET_PASSWORD:
                self.send_json_response(200, {"status": "authenticated", "token": "session_token"})
            else:
                self.send_json_response(401, {"error": "Invalid password"})

        elif parsed_path.path == "/api/chat/ndfl":
            message = data.get("message", "")
            history = data.get("history", [])
            response_text = self._call_openrouter(message, history, "ndfl")
            self.send_json_response(200, {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })

        elif parsed_path.path == "/api/chat/taxes":
            message = data.get("message", "")
            history = data.get("history", [])
            response_text = self._call_openrouter(message, history, "taxes")
            self.send_json_response(200, {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
        else:
            self.send_json_response(404, {"error": "Not found"})

    def _call_openrouter(self, message, history, mode):
        """Вызов OpenRouter API"""

        system_prompt = self._get_system_prompt(mode)

        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg.get("role"), "content": msg.get("content")})

        messages.append({"role": "user", "content": message})

        payload = {
            "model": "anthropic/claude-opus-4-8",
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": 0.7 if mode == "ndfl" else 0.5,
            "max_tokens": 1000,
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://accounting-assistant.local",
            "X-Title": "Accounting Assistant",
        }

        try:
            print(f"[OPENROUTER] Отправляю запрос к {OPENROUTER_BASE_URL}/chat/completions")
            print(f"[OPENROUTER] API Key: {OPENROUTER_API_KEY[:20]}...")

            req = urllib.request.Request(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                data=json.dumps(payload).encode(),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"[OPENROUTER ERROR] {e.code}: {error_body}")
            return f"❌ OpenRouter: {e.code} - {error_body[:100]}"
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {str(e)}")
            return f"❌ Ошибка: {str(e)}"

    def _get_system_prompt(self, mode):
        if mode == "ndfl":
            return """Ты — помощник бухгалтера в строительной компании.

ТВОЯ ОСНОВНАЯ ЗАДАЧА: Проверять расчёты НДФЛ из зарплат сотрудников.

Когда бухгалтер предоставляет данные о зарплате, ты должен:
1. Проверить правильность расчёта НДФЛ (13% от налоговой базы)
2. Указать, правильно ли удержан налог
3. Если ошибка — объяснить, на какую сумму и почему

Налоговые ставки на 2024 год в РФ:
- НДФЛ: 13% (резидент) или 30% (нерезидент)
- ЕСН пенсия: 22%
- ЕСН медицина: 5.1%
- ЕСН социальное: 2.9%

Ответ должен быть точный, с цифрами и объяснением."""
        else:
            return """Ты — налоговый консультант для бухгалтера в строительной компании.

Ты отвечаешь на вопросы про:
- Налоги в строительстве (НДС, налог на прибыль, социальные взносы)
- Какие документы нужны для разных операций
- Правильность оформления зарплаты и удержаний
- Налоговые льготы в строительстве

Ответы должны быть:
- Точные и ссылаться на актуальные нормы (2024)
- На русском языке
- С примерами, если нужны цифры
- Краткие, но полные"""

    def do_OPTIONS(self):
        """Обработка CORS preflight"""
        print(f"[OPTIONS] {self.path}")  # DEBUG
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Кастомный лог"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")


if __name__ == "__main__":
    PORT = 8000
    print(f"🔑 API Key загружен: {OPENROUTER_API_KEY[:30]}...")
    server = HTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"🚀 Сервер запущен на http://localhost:{PORT}")
    print(f"📚 API документация: http://localhost:{PORT}/api/health")
    print(f"🔑 Используется пароль: {SECRET_PASSWORD}")
    print(f"⏹️  Для остановки нажми Ctrl+C")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Сервер остановлен")
        sys.exit(0)
