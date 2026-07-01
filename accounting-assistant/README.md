# Accounting Assistant 🧮

Веб-ассистент для бухгалтера в строительной компании. Помогает проверять расчёты НДФЛ, консультирует по налогам и хранит историю диалогов.

## Основные функции

- ✅ **Проверка НДФЛ** — загрузи Excel с зарплатой, ассистент проверит правильность удержаний
- ✅ **Консультации по налогам** — вопросы про НДС, социальные взносы, налог на прибыль в строительстве
- ✅ **История диалогов** — все разговоры сохраняются в БД
- ✅ **Анализ файлов** — загрузка и парсинг Excel-файлов
- ⏳ **Интеграция 1C** — автоматическая синхронизация данных о зарплатах (вторая фаза)

## Требования

- **Python 3.10+** (backend)
- **Node.js 18+** (frontend)
- **PostgreSQL** или **SQLite** (для БД)
- **OpenRouter API key** (для ИИ)

## Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone <repo-url>
cd accounting-assistant
```

### 2. Установи зависимости

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Настрой переменные окружения

**Backend** (`.env`):
```
OPENROUTER_API_KEY=sk-or-...
DATABASE_URL=sqlite:///./data.db
SECRET_KEY=твой_пароль_для_входа
DEBUG=False
```

**Frontend** (`.env`):
```
VITE_API_URL=http://localhost:8000
```

### 4. Запусти приложение

**Backend:**
```bash
cd backend
python main.py
```

**Frontend** (в другом терминале):
```bash
cd frontend
npm run dev
```

Приложение будет доступно на `http://localhost:3030`

## Архитектура

```
accounting-assistant/
├── backend/                  # FastAPI приложение
│   ├── main.py              # Точка входа
│   ├── api/                 # API endpoints
│   ├── models/              # Модели БД (SQLAlchemy)
│   ├── services/            # Бизнес-логика
│   ├── prompts/             # Промпты для ИИ
│   └── requirements.txt
│
├── frontend/                # React приложение
│   ├── src/
│   ├── public/
│   └── package.json
│
├── CLAUDE.md               # Принципы разработки проекта
├── 1C-API-SETUP-GUIDE.md   # Инструкция для админа 1C
└── README.md               # Этот файл
```

## API Endpoints

- `GET /api/health` — проверка здоровья приложения
- `POST /api/chat` — отправить сообщение ассистенту
- `GET /api/history` — история диалогов
- `POST /api/upload` — загрузка Excel-файла
- `GET /api/tax-rates` — справочник налоговых ставок

## Интеграция с 1C

См. подробную инструкцию в [`1C-API-SETUP-GUIDE.md`](1C-API-SETUP-GUIDE.md)

**Кратко:**
1. 1C-администратор настраивает HTTP-сервис в 1С:Бухгалтерия 8.3
2. Ассистент получает доступ к данным о сотрудниках и зарплатах
3. Данные синхронизируются и кэшируются на сервере

## Безопасность

- Пароль хранится в переменной окружения (не в коде)
- Данные о зарплатах шифруются при хранении (если критично)
- Все запросы логируются
- Резервные копии БД делаются автоматически

## Развёртывание

### Локально на VPS компании

```bash
# Через Docker (рекомендуется)
docker-compose up -d

# Или вручную через systemd
sudo systemctl start accounting-assistant
```

### Мониторинг

- Логи: `/var/log/accounting-assistant.log`
- БД: `/data/accounting-assistant.db` (SQLite)
- Health check: `curl http://localhost:8000/api/health`

## Разработка

### Тестирование

```bash
cd backend
pytest tests/
```

### Linting и форматирование

```bash
black backend/
flake8 backend/
```

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| "OpenRouter API key not found" | Проверь переменную окружения `OPENROUTER_API_KEY` |
| "Database locked" | Закрой все открытые соединения, перезагрузи приложение |
| "Excel не парсится" | Убедись, что файл в формате `.xlsx` (не `.xls`), не защищён паролем |
| "Ассистент отвечает неправильно" | Обнови промпты в `backend/prompts/` |

## План развития

**Фаза 1 (текущая):** MVP с загрузкой файлов  
**Фаза 2:** Интеграция с 1C API  
**Фаза 3:** Экспорт отчётов и аналитика  
**Фаза 4:** Мобильный интерфейс (может быть)

## Поддержка

Вопросы или баги? Свяжись с Александром Прохоровым.

---

**Версия:** 1.0.0-alpha  
**Последнее обновление:** 01.07.2026  
**Статус:** В разработке MVP
