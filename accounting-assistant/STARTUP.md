# 🚀 Запуск Accounting Assistant (MVP)

## Требования

- **Python 3.10+**
- **Node.js 18+**
- **OpenRouter API key** (получи на https://openrouter.ai)

---

## Шаг 1: Подготовка Backend

### 1.1 Создать виртуальное окружение

```bash
cd backend
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 1.2 Установить зависимости

```bash
pip install -r requirements.txt
```

### 1.3 Создать .env файл

Скопируй `.env.example` и заполни:

```bash
cp ../.env.example ../.env
```

Затем отредактируй `../.env`:

```
OPENROUTER_API_KEY=sk-or-YOUR_KEY_HERE
SECRET_KEY=твой_пароль_для_входа
DATABASE_URL=sqlite:///./data.db
DEBUG=True
```

**Где получить OPENROUTER_API_KEY:**
1. Перейди на https://openrouter.ai
2. Зарегистрируйся
3. Перейди в Settings → API Keys
4. Создай новый ключ
5. Скопируй его в `.env`

### 1.4 Запустить backend

```bash
python main.py
```

Если всё работает, увидишь:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Проверка здоровья:**
```bash
curl http://localhost:8000/api/health
```

---

## Шаг 2: Подготовка Frontend

### 2.1 Установить зависимости

```bash
cd frontend
npm install
```

### 2.2 Создать .env файл

```bash
cp .env.example .env
```

Содержимое (по умолчанию OK):
```
VITE_API_URL=http://localhost:8000
```

### 2.3 Запустить dev-сервер

```bash
npm run dev
```

Увидишь:
```
VITE v5.0.8  ready in 123 ms
➜  Local:   http://localhost:3030/
```

---

## Шаг 3: Открыть приложение

1. Открой браузер: http://localhost:3030
2. Введи пароль (тот, что указал в `SECRET_KEY`)
3. Готово! 🎉

---

## Тестирование MVP

### Режим 1: Проверка НДФЛ

1. Переключись на режим **💰 Проверка НДФЛ**
2. Загрузи Excel-файл с зарплатой (пример структуры ниже)
3. Задай вопрос: "Проверь правильность расчёта НДФЛ"

**Пример Excel структуры:**
```
| ФИО          | Оклад | НДФЛ  |
|--------------|-------|-------|
| Иван Петров  | 50000 | 6500  |
| Мария Сидор  | 60000 | 7800  |
```

### Режим 2: Консультация по налогам

1. Переключись на режим **📋 Консультация по налогам**
2. Спроси: "Какой налог на зарплату в строительстве?"
3. Ассистент ответит с актуальной информацией

---

## Troubleshooting

### Ошибка: "OPENROUTER_API_KEY not found"

**Решение:** Проверь, что `.env` файл находится в корне проекта (`accounting-assistant/.env`), не в `backend/`.

### Ошибка: "Address already in use"

**Решение:** Порт 8000 или 3000 заняты.
```bash
# Убей процесс на порту 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Ошибка: "CORS error"

**Решение:** Frontend и backend должны быть на одних и тех же машинах или frontend должен быть на localhost:3000, backend на localhost:8000.

### Ошибка: "Cannot find module"

**Решение:** Убедись, что установил зависимости:
```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

---

## Остановка приложения

**Backend:** Нажми `Ctrl+C` в терминале backend

**Frontend:** Нажми `Ctrl+C` в терминале frontend

---

## Что дальше?

После тестирования MVP:

1. **Интеграция 1C:** Отправь инструкцию админу (`1C-API-SETUP-GUIDE.md`)
2. **Расширение функций:** Добавь аналитику, экспорт отчётов
3. **Развёртывание:** Развёрни на VPS компании (195.2.85.114)

---

## Полезные команды

```bash
# Backend: переустановить зависимости
cd backend
pip install --upgrade -r requirements.txt

# Frontend: очистить кэш и переустановить
cd frontend
rm -rf node_modules package-lock.json
npm install

# Проверка linting (backend)
cd backend
flake8 main.py

# Форматирование (backend)
cd backend
black main.py
```

---

**Вопросы?** Связь с разработчиком: Александр Прохоров
