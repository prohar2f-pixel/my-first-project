# Проекты

### AI Design Platform (ChatGPT → Figma → Tilda)
- Стек: HTML/CSS/JS без фреймворков, Figma REST API, Runware API (медиа), Tilda API, OpenAI/Anthropic API
- Статус: спецификация готова (docs/specs/2026-06-15-ai-design-platform.md в репо my-first-project), разработка не начата
- Репо: github.com/prohar2f-pixel/my-first-project (клон на сервере: ~/projects/my-first-project), полный спек — knowledge/ai-design-platform-spec.md
- Что дальше: Этап 0 (получить API-ключи Runware/Figma/Tilda/Anthropic) → Этап 1 (Runware медиа-инструмент)

### Сайт "Все туры" (prohar2f-pixel.github.io)
- Стек: статический HTML/CSS/JS, WebGL fluid-анимация, Cloudflare Worker (проксирует форму в Telegram)
- Статус: production, опубликован на GitHub Pages
- Репо: github.com/prohar2f-pixel/my-first-project (тот же репо, корень) и github.com/prohar2f-pixel/prohar2f-pixel.github.io
- Что дальше: план 10/10 фиксов (docs/superpowers/plans/2026-06-15-website-10-10.md) — судя по наличию cloudflare-worker/, в основном выполнен

### Freelance Monitor Bot
- Стек: Python, Telegram (Telethon/Bot API), мониторит FL.ru / Habr Freelance / Kwork / Telegram-каналы
- Статус: рабочий прототип
- Репо: github.com/prohar2f-pixel/my-first-project/freelance-bot (клон на сервере: ~/projects/my-first-project/freelance-bot)
- Что дальше: не зафиксировано — уточнить у клиента при следующей сессии

### Smeta Bot — поиск цен на стройматериалы
- Стек: python-telegram-bot, Anthropic API (анализ PDF/извлечение данных), pdfplumber, Serper API (поиск), openpyxl (Excel-отчёт)
- Статус: работает в production на Railway. Код полностью готов (12 коммитов). Ключ Claude был обрезан/устарел при первой вставке (401 invalid x-api-key) — пересоздан в console.anthropic.com и обновлён в Railway, /test прошёл успешно
- Репо: github.com/prohar2f-pixel/my-first-project/smeta-bot (клон на сервере: ~/projects/my-first-project/smeta-bot)
- Что дальше: не зафиксировано — уточнить у клиента при следующей сессии

### ТЗ-бот (tzbot)
- Стек: Python, python-telegram-bot, Anthropic API, PostgreSQL (psycopg2), деплой на Railway
- Статус: в разработке (судя по коду — рабочий, есть Procfile для деплоя)
- Репо: github.com/prohar2f-pixel/my-first-project/tzbot (клон на сервере: ~/projects/my-first-project/tzbot)
- Что дальше: не зафиксировано — уточнить у клиента при следующей сессии

## Шаблон проекта

<!-- Копируй этот блок для каждого нового проекта -->
<!--
### Название проекта
- Стек:
- Статус: идея / в разработке / production
- Репо:
- Что дальше:
-->
