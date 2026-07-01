import os
import json
import urllib.request
import urllib.error
from datetime import datetime
import logging
from typing import Optional, List

# Загрузить переменные окружения из .env
def load_env():
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SECRET_PASSWORD = os.getenv("SECRET_KEY", "default_password")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

# Импортируем FastAPI если доступен, иначе используем встроенный HTTP сервер
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI не установлен, используется упрощённая версия")

# Модели данных
from pydantic import BaseModel
from typing import Optional, List

class Message(BaseModel):
    role: str  # "user" или "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = None

class AuthRequest(BaseModel):
    password: str

class TaxRates(BaseModel):
    ндфл: float = 13.0
    ес_взнос_пенс: float = 22.0
    ес_взнос_мед: float = 5.1
    ес_взнос_соц: float = 2.9
    ес_взнос_безопасность: float = 0.3

# Промпты для ИИ
SYSTEM_PROMPT_НДФЛ = """Ты — помощник бухгалтера в строительной компании.

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
- ЕСН безопасность: 0.3%

Ответ должен быть точный, с цифрами и объяснением."""

SYSTEM_PROMPT_НАЛОГИ = """Ты — налоговый консультант для бухгалтера в строительной компании.

Ты отвечаешь на вопросы про:
- Налоги в строительстве (НДС, налог на прибыль, социальные взносы)
- Какие документы нужны для разных операций
- Правильность оформления зарплаты и удержаний
- Налоговые льготы и льготы в строительстве

Ответы должны быть:
- Точные и ссылаться на актуальные нормы (2024)
- На русском языке
- С примерами, если нужны цифры
- Краткие, но полные"""

# API endpoints

@app.get("/api/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/auth")
async def authenticate(auth: AuthRequest):
    """Аутентификация бухгалтера"""
    if auth.password != SECRET_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "status": "authenticated",
        "token": "session_token"  # TODO: реальные токены
    }

@app.get("/api/tax-rates")
async def get_tax_rates():
    """Получить справочник налоговых ставок на 2024"""
    return TaxRates()

@app.post("/api/chat/ndfl")
async def chat_ndfl(request: ChatRequest):
    """Проверка НДФЛ через ИИ"""
    logger.info(f"НДФЛ запрос: {request.message[:50]}...")

    # Построить историю сообщений для OpenRouter
    messages = []

    if request.history:
        for msg in request.history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

    messages.append({
        "role": "user",
        "content": request.message
    })

    # Запрос к OpenRouter API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://accounting-assistant.local",
                    "X-Title": "Accounting Assistant",
                },
                json={
                    "model": "claude-opus-4-8",
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT_НДФЛ
                        },
                        *messages
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }
            )

        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.text}")
            raise HTTPException(status_code=500, detail="AI service error")

        result = response.json()
        ai_message = result["choices"][0]["message"]["content"]

        return {
            "role": "assistant",
            "content": ai_message,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/taxes")
async def chat_taxes(request: ChatRequest):
    """Консультация по налогам"""
    logger.info(f"Налоговый вопрос: {request.message[:50]}...")

    messages = []

    if request.history:
        for msg in request.history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

    messages.append({
        "role": "user",
        "content": request.message
    })

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://accounting-assistant.local",
                    "X-Title": "Accounting Assistant",
                },
                json={
                    "model": "claude-opus-4-8",
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT_НАЛОГИ
                        },
                        *messages
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1000,
                }
            )

        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.text}")
            raise HTTPException(status_code=500, detail="AI service error")

        result = response.json()
        ai_message = result["choices"][0]["message"]["content"]

        return {
            "role": "assistant",
            "content": ai_message,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/excel")
async def upload_excel(file: UploadFile = File(...)):
    """Загрузка и парсинг Excel файла с зарплатой"""

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files allowed")

    try:
        # Читаем файл
        contents = await file.read()

        # Парсим Excel
        df = pd.read_excel(contents)

        # Преобразуем в JSON
        data = df.to_dict(orient='records')

        logger.info(f"Excel файл загружен: {len(data)} строк")

        return {
            "status": "success",
            "filename": file.filename,
            "rows": len(data),
            "data": data,
            "columns": list(df.columns)
        }

    except Exception as e:
        logger.error(f"Error parsing Excel: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
