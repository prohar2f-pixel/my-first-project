# Как задеплоить AI Генератор — пошаговый гайд

Это инструкция от начала до конца. Делай по порядку, ничего не пропускай.

---

## Шаг 1 — Получи API ключ Runware

1. Зайди на https://runware.ai
2. Зарегистрируйся или войди
3. Зайди в раздел API Keys (в настройках аккаунта)
4. Создай новый ключ, скопируй его — он нужен будет в Шаге 4

---

## Шаг 2 — Задеплой бэкенд на Railway

**2.1 — Создай аккаунт на Railway**

Зайди на https://railway.app и войди через GitHub.

**2.2 — Создай новый проект**

1. Нажми **"New Project"**
2. Выбери **"Deploy from GitHub repo"**
3. Выбери репозиторий `my-first-project`
4. Railway спросит какую папку деплоить — нажми **"Configure"** и в поле **Root Directory** напиши:
   ```
   image-gen-api
   ```
5. Нажми **Deploy**

> Если Railway сам не нашёл настройки — ничего страшного, они в файле `nixpacks.toml` который уже лежит в папке.

**2.3 — Добавь базу данных PostgreSQL**

1. В проекте на Railway нажми **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway сам создаст базу и добавит переменную `DATABASE_URL` в твой сервис — ничего дополнительно делать не нужно

---

## Шаг 3 — Придумай секретный ключ для JWT

Открой PowerShell и запусти:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Получишь что-то вроде:
```
a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
```

Скопируй это — это твой `JWT_SECRET`.

---

## Шаг 4 — Пропиши переменные окружения на Railway

1. В Railway зайди в свой сервис (не в базу, а в сам бэкенд)
2. Нажми вкладку **"Variables"**
3. Добавь эти переменные одну за одной (кнопка **"New Variable"**):

| Имя переменной | Значение |
|----------------|----------|
| `RUNWARE_API_KEY` | твой ключ из Шага 1 |
| `JWT_SECRET` | случайная строка из Шага 3 |
| `ADMIN_USERNAME` | придумай логин для себя (например `prohar`) |
| `ADMIN_PASSWORD` | придумай пароль (не менее 10 символов) |
| `SEED_ADMIN` | `true` |

> `DATABASE_URL` Railway добавил сам в Шаге 2.3 — его не нужно трогать.

4. После добавления всех переменных Railway автоматически перезапустит сервис

---

## Шаг 5 — Узнай URL твоего бэкенда

1. В Railway зайди в свой сервис
2. Нажми вкладку **"Settings"**
3. В разделе **"Domains"** нажми **"Generate Domain"** (если домен ещё не создан)
4. Скопируй URL — он выглядит примерно так:
   ```
   https://my-first-project-production-xxxx.up.railway.app
   ```

---

## Шаг 6 — Вставь URL в HTML файлы

Открой PowerShell и запусти (замени URL на свой из Шага 5):

```powershell
cd "C:\Users\Udacha\Documents\projects\my-first-project"

$url = "https://my-first-project-production-xxxx.up.railway.app"

(Get-Content image-gen\login.html) -replace 'REPLACE_WITH_RAILWAY_URL', $url | Set-Content image-gen\login.html -Encoding utf8
(Get-Content image-gen\index.html) -replace 'REPLACE_WITH_RAILWAY_URL', $url | Set-Content image-gen\index.html -Encoding utf8
(Get-Content image-gen\admin.html) -replace 'REPLACE_WITH_RAILWAY_URL', $url | Set-Content image-gen\admin.html -Encoding utf8
```

Проверь что замена сработала:

```powershell
Select-String -Path "image-gen\login.html" -Pattern "railway.app"
```

Должна показаться строка с твоим URL.

---

## Шаг 7 — Закоммить и запушить на GitHub

```powershell
cd "C:\Users\Udacha\Documents\projects\my-first-project"

git add image-gen/
git commit -m "feat(image-gen): set Railway API URL"
git checkout main
git merge feat/image-gen
git push
```

После этого Netlify автоматически задеплоит фронтенд (обычно 1-2 минуты).

---

## Шаг 8 — Проверь что всё работает

1. Зайди на `https://твой-сайт.netlify.app/image-gen/login.html`
2. Войди с логином и паролем которые ты задал в Шаге 4 (ADMIN_USERNAME / ADMIN_PASSWORD)
3. Ты попадёшь на страницу администратора
4. Создай тестового клиента — нажми "Создать", введи логин/пароль/кредиты
5. Выйди и войди как этот клиент
6. Попробуй сгенерировать картинку — введи промпт и нажми кнопку

---

## Если что-то пошло не так

**Бэкенд не запускается на Railway:**
- Зайди в Railway → твой сервис → вкладка "Logs"
- Посмотри на ошибку
- Чаще всего причина: не заполнены переменные или неправильный Root Directory

**Ошибка при генерации "RUNWARE_API_KEY not set":**
- Зайди в Railway → Variables → проверь что `RUNWARE_API_KEY` есть и не пустой

**Страница не открывается / белый экран:**
- Открой DevTools в браузере (F12) → вкладка Console
- Посмотри ошибки — скорее всего URL неправильный (не заменил REPLACE_WITH_RAILWAY_URL)

**Не могу войти (неверный логин/пароль):**
- Проверь переменные `ADMIN_USERNAME` и `ADMIN_PASSWORD` на Railway
- Или посмотри в Logs — был ли запущен SEED_ADMIN при старте

---

## Итог — что где лежит

| Что | Где |
|-----|-----|
| Бэкенд (Python API) | Railway |
| База данных | Railway (PostgreSQL) |
| Фронтенд (HTML страницы) | Netlify |
| Страница входа | `https://твой-сайт/image-gen/login.html` |
| Страница генератора | `https://твой-сайт/image-gen/index.html` |
| Панель администратора | `https://твой-сайт/image-gen/admin.html` |
