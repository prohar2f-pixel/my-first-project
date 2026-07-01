# Accounting Assistant 🧮

Веб-ассистент для бухгалтера в строительной компании. Помогает проверять расчёты НДФЛ, консультирует по налогам, хранит историю диалогов.

## ✨ Функции

- ✅ **Проверка НДФЛ** — загрузи Excel с зарплатой, ассистент проверит правильность расчётов
- ✅ **Консультации по налогам** — ответы на вопросы про НДС, социальные взносы, налог на прибыль
- ✅ **История диалогов** — все разговоры сохраняются в БД
- ✅ **Загрузка файлов** — поддержка Excel, PDF, Word
- ⏳ **Интеграция 1C** — автоматическая синхронизация данных (вторая фаза)

## 🚀 Быстрый старт

### Самый простой способ

Открой **`START.bat`** в корне проекта. Оба сервера запустятся в новых окнах.

Потом открой браузер: **http://localhost:3030**

Пароль: **`123`**

---

### Ручной запуск (для разработки)

**Terminal 1 — Backend:**
```powershell
cd backend
$env:PYTHONIOENCODING = "utf-8"
python simple_server.py
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev -- --host 0.0.0.0
```

Откроется на **http://localhost:3030** (или **http://localhost:3031** если 3030 занят)

---

## 📋 Требования

- **Python 3.10+** (backend работает на встроенных модулях)
- **Node.js 18+** (frontend)
- **OpenRouter API key** (получи на https://openrouter.ai)

---

## ⚙️ Конфигурация

### Backend (файл `backend/.env`)

```env
OPENROUTER_API_KEY=sk-or-v1-ххххххххххххххххххххххххххххх
SECRET_KEY=123
DATABASE_URL=sqlite:///./data.db
DEBUG=True
```

### Frontend (файл `frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

---

## 🔐 Безопасность

⚠️ **ВАЖНО:** Файлы `.env` добавлены в `.gitignore` — они никогда не попадут в гит!

Никогда не коммитьте:
- `.env` файлы
- API ключи
- Пароли
- Приватные данные

---

## 📁 Структура проекта

```
accounting-assistant/
├── CLAUDE.md                    # Принципы разработки
├── 1C-API-SETUP-GUIDE.md        # Инструкция для админа 1C
├── STARTUP.md                   # Подробный гайд запуска
├── START.bat                    # Скрипт автозапуска (Windows)
├── README.md                    # Этот файл
│
├── backend/
│   ├── simple_server.py         # HTTP сервер (встроенные модули Python)
│   ├── .env                     # Переменные окружения (в .gitignore!)
│   └── ...
│
└── frontend/
    ├── src/
    │   ├── App.tsx              # Главный компонент
    │   ├── App.css              # Стили
    │   └── main.tsx
    ├── package.json
    ├── .env                     # Переменные окружения (в .gitignore!)
    └── ...
```

---

## API Endpoints

- `GET /api/health` — проверка здоровья приложения
- `POST /api/auth` — вход (пароль)
- `POST /api/chat/ndfl` — консультация по НДФЛ
- `POST /api/chat/taxes` — консультация по налогам
- `POST /api/upload/excel` — загрузка файла
- `GET /api/tax-rates` — справочник налоговых ставок

---

## 🐛 Troubleshooting

| Проблема | Решение |
|----------|---------|
| "ERR_CONNECTION_REFUSED" | Проверь, запущены ли backend и frontend |
| "Страница не найдена" | Очисти кэш браузера (Ctrl+Shift+Delete) или открой в incognito |
| "Неверный пароль" | Пароль по умолчанию: `123` (измени в `backend/.env` → `SECRET_KEY`) |
| "OpenRouter API error 401" | Проверь OPENROUTER_API_KEY в `backend/.env` |
| Порт 3030 занят | Frontend использует следующий свободный порт (3031, 3032...) |

---

## 📚 Дополнительно

- Подробный гайд запуска: [`STARTUP.md`](STARTUP.md)
- Принципы разработки: [`CLAUDE.md`](CLAUDE.md)
- Настройка 1C интеграции: [`1C-API-SETUP-GUIDE.md`](1C-API-SETUP-GUIDE.md)

---

**Версия:** 1.0.0  
**Статус:** MVP (рабочая версия)  
**Последнее обновление:** 02.07.2026
