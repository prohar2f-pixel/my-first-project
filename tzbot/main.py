import os
import asyncio
import logging
import json
import base64
import re
import signal
from io import BytesIO
from datetime import date

import psycopg2
import psycopg2.pool

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.error import Conflict
from openai import OpenAI
import asr

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN     = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
ALEXANDER_CHAT_ID  = int(os.environ["ALEXANDER_CHAT_ID"])

# OpenRouter (OpenAI-совместимый шлюз). Модель меняется одной переменной LLM_MODEL.
LLM_MODEL = os.environ.get("LLM_MODEL", "anthropic/claude-haiku-4.5")
llm = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

URL_RE   = re.compile(r'https?://[^\s]+')
TOPIC_RE = re.compile(r'\[ТЕМА:(\d+)\]')

TOPIC_NAMES = {
    1: "О бизнесе",
    2: "Дизайн и стиль",
    3: "Структура сайта",
    4: "Контент",
    5: "Интеграции",
    6: "Данные клиентов",
    7: "Воронки",
    8: "Ваш контакт",
}

TOPIC_NAMES_AI = {
    1: "Бизнес и задача",
    2: "Пользователи",
    3: "Функции ИИ",
    4: "Данные и знания",
    5: "Интерфейс",
    6: "Память",
    7: "Ограничения",
    8: "Запуск",
}

TOPIC_NAMES_TG = {
    1: "Цель бота",
    2: "Аудитория",
    3: "Функции",
    4: "Контент и данные",
    5: "Интеграции",
    6: "Данные пользователей",
    7: "Монетизация",
    8: "Контакт",
}

TOPIC_NAMES_MINIAPP = {
    1: "Цель и задача",
    2: "Аудитория",
    3: "Экраны и путь",
    4: "Запись и оплата",
    5: "Контент",
    6: "Внешний вид",
    7: "После действия",
    8: "Контакт",
}

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


# ─── DATABASE ─────────────────────────────────────────────────────────────────

def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(1, 10, os.environ["DATABASE_URL"])
    return _pool


def _exec(sql: str, params: tuple = (), fetch: bool = False):
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchone() if fetch else None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def db_init():
    _exec("""
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id    BIGINT PRIMARY KEY,
            site_type  TEXT,
            first_msg  TEXT DEFAULT '',
            steps      TEXT DEFAULT '[]',
            cur_q      TEXT DEFAULT '',
            pending_tz TEXT DEFAULT '',
            updated_at BIGINT DEFAULT extract(epoch from now())::BIGINT
        )
    """)
    try:
        _exec("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS pending_tz TEXT DEFAULT ''")
    except Exception:
        pass


def db_get(chat_id: int) -> dict | None:
    row = _exec(
        "SELECT site_type, first_msg, steps, cur_q, pending_tz FROM sessions WHERE chat_id=%s",
        (chat_id,), fetch=True
    )
    if not row:
        return None
    return {
        "site_type":  row[0],
        "first_msg":  row[1],
        "steps":      json.loads(row[2]),
        "cur_q":      row[3],
        "pending_tz": row[4] or "",
    }


def db_save(chat_id: int, *, site_type: str, first_msg: str,
            steps: list, cur_q: str, pending_tz: str = ""):
    _exec("""
        INSERT INTO sessions (chat_id, site_type, first_msg, steps, cur_q, pending_tz)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET
            site_type  = EXCLUDED.site_type,
            first_msg  = EXCLUDED.first_msg,
            steps      = EXCLUDED.steps,
            cur_q      = EXCLUDED.cur_q,
            pending_tz = EXCLUDED.pending_tz,
            updated_at = extract(epoch from now())::BIGINT
    """, (chat_id, site_type, first_msg,
          json.dumps(steps, ensure_ascii=False), cur_q, pending_tz))


def db_delete(chat_id: int):
    _exec("DELETE FROM sessions WHERE chat_id=%s", (chat_id,))


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

SITE_TYPES = {
    "landing":    "🎯 Лендинг",
    "shop":       "🛒 Интернет-магазин",
    "corporate":  "🏢 Корпоративный сайт",
    "portfolio":  "🎨 Портфолио",
    "vizitka":    "💼 Сайт-визитка",
    "other":      "💡 Другой тип",
    "ai_agent":   "🤖 ИИ Ассистент",
    "tg_bot":     "📱 Telegram Бот",
    "tg_miniapp": "📲 Telegram Mini App",
}

BASE_SYSTEM = f"""Ты помогаешь человеку описать его будущий сайт, чтобы потом разработчик Александр Прохоров мог его сделать.

Сегодняшняя дата: {date.today().strftime('%d.%m.%Y')}

## КАК ОБЩАТЬСЯ
Говори как друг — просто, тепло, без умных слов. Представь что объясняешь бабушке.
Никакого жаргона. Конкретные замены:
- не "интеграции" — а "форма 'Напишите нам', оплата картой на сайте, онлайн-чат"
- не "воронка продаж" — а "как посетитель становится клиентом"
- не "CRM" — а "программа для учёта клиентов"
- не "конверсия" — а "сколько людей оставят заявку"
- не "pop-up" — а "всплывающее окошко"
- не "контент" — а "тексты и фотографии"
- не "целевая аудитория" — а "для кого этот сайт"
Если человек не понял вопрос — переформулируй проще, без извинений.

## ЧТО НУЖНО УЗНАТЬ (8 шагов):
1. Бизнес — чем занимается, кто его клиенты, зачем нужен сайт
2. Внешний вид — какой стиль нравится, цвета, есть ли сайты которые нравятся как образец
3. Разделы сайта — что должно быть на сайте (например: о нас, услуги, цены, портфолио, контакты)
4. Материалы — что уже есть (тексты, фотографии, логотип), а что нужно сделать с нуля
5. Кнопки и формы — нужна ли кнопка "Заказать звонок", форма заявки, оплата на сайте, карта проезда
6. Что узнаём о посетителях — имя, телефон или email — что хочет собирать со своих клиентов
7. Как привлекаем — нужны ли кнопки "Купить сейчас", всплывающие окошки, автоответ на заявку
8. Контакт — как зовут человека и как с ним связаться после

## ПРАВИЛА
- НАЧИНАЙ каждый свой ответ с маркера текущей темы: [ТЕМА:N] — например [ТЕМА:2]
- Начни с тёплого приветствия и первого вопроса о бизнесе
- Один вопрос за раз — никогда не задавай несколько сразу
- Если прислали картинку — скажи что увидел, продолжи разговор
- Если прислали ссылку — скажи что за сайт, продолжи разговор
- Если ответ непонятный — уточни другими словами

## КОГДА ВСЕ 8 ШАГОВ ПРОЙДЕНЫ:
Напиши строго в таком формате — сначала проверку, потом ТЗ:

[ТЕМА:8]
ТЗ_ПРОВЕРКА
Вот что я узнал о вашем проекте:
• Бизнес: [коротко]
• Для кого сайт: [коротко]
• Внешний вид: [коротко]
• Разделы: [коротко]
• Материалы: [коротко]
• Кнопки и формы: [коротко]
• Сбор контактов: [коротко]
• Контакт клиента: [имя и контакт]
ТЗ_ГОТОВО
# Техническое задание на разработку сайта
Дата: {date.today().strftime('%d.%m.%Y')}

## 1. О бизнесе
[подробно]

## 2. Цель сайта
[подробно]

## 3. Для кого сайт
[подробно]

## 4. Внешний вид и стиль
[цвета, настроение, примеры]

## 5. Структура сайта
[список разделов с кратким описанием]

## 6. Материалы
[что есть, что нужно подготовить]

## 7. Формы, кнопки, оплата
[список]

## 8. Сбор контактов посетителей
[поля форм]

## 9. Как привлекаем клиентов
[кнопки, всплывающие окошки, автоответы]

## 10. Дополнительные пожелания
[всё остальное]

## 11. Контактные данные клиента
[имя и способ связи]"""

SITE_TYPE_HINTS = {
    "landing":   "Человек хочет одностраничный сайт для продажи одного товара или услуги. Спрашивай про главное предложение, цену, почему должны выбрать именно его, и как человек оставит заявку.",
    "shop":      "Человек хочет интернет-магазин. Уточни: сколько товаров, как сортировать, нужна ли оплата картой прямо на сайте, как будет доставка, нужен ли личный кабинет покупателя.",
    "corporate": "Человек хочет сайт для компании. Спрашивай про разделы: о компании, команда, услуги, новости, контакты.",
    "portfolio": "Человек хочет показать свои работы. Уточни: какие работы показывать, нужен ли блог, как потенциальный клиент может написать.",
    "vizitka":   "Человек хочет простой сайт-визитку (1–3 страницы). Главное: чем занимается, как связаться, форма заявки.",
    "other":     "Сначала уточни что именно хочет человек — какой сайт, для чего.",
}


AI_AGENT_SYSTEM = f"""Ты помогаешь человеку описать его будущего ИИ-помощника, чтобы потом разработчик Александр Прохоров мог его сделать.

Сегодняшняя дата: {date.today().strftime('%d.%m.%Y')}

## КАК ОБЩАТЬСЯ
Говори как друг — просто, тепло, без умных слов. Представь что объясняешь бабушке.
Никакого жаргона. Конкретные замены:
- не "ИИ-ассистент" — а "умный помощник который отвечает на вопросы"
- не "интерфейс" — а "где будет работать — в Telegram, на сайте или ещё где-то"
- не "база знаний" — а "документы или тексты откуда он будет брать ответы"
- не "персонализация" — а "будет ли он помнить с кем разговаривал"
- не "API" — а "соединение с другими программами"
- не "конфиденциально" — а "секретная информация которую нельзя никому говорить"
Если человек не понял вопрос — переформулируй проще, без извинений.

## ЧТО НУЖНО УЗНАТЬ (8 шагов):
1. Бизнес и задача — чем занимается, какую проблему должен решать этот помощник
2. Кто будет пользоваться — его клиенты? сотрудники? он сам?
3. Что делает помощник — отвечает на вопросы? пишет тексты? считает? принимает заказы?
4. Откуда берёт информацию — из каких документов или сайтов он должен отвечать
5. Где будет работать — в Telegram, на сайте, в WhatsApp или ещё где-то
6. Будет ли помнить людей — или каждый раз разговор начинается заново
7. Что нельзя — о чём нельзя говорить, какая информация секретная
8. Сроки и контакт — когда нужно, бюджет если есть, как зовут и как связаться

## ПРАВИЛА
- НАЧИНАЙ каждый свой ответ с маркера текущей темы: [ТЕМА:N] — например [ТЕМА:3]
- Начни с тёплого приветствия и первого вопроса про бизнес
- Один вопрос за раз — никогда не задавай несколько сразу
- Если ответ непонятный — уточни другими словами

## КОГДА ВСЕ 8 ШАГОВ ПРОЙДЕНЫ:
Напиши строго в таком формате:

[ТЕМА:8]
ТЗ_ПРОВЕРКА
Вот что я узнал о вашем проекте:
• Задача: [коротко]
• Кто пользуется: [коротко]
• Что делает: [коротко]
• Откуда знает ответы: [коротко]
• Где работает: [коротко]
• Память: [коротко]
• Ограничения: [коротко]
• Контакт: [имя и контакт]
ТЗ_ГОТОВО
# Техническое задание на разработку ИИ-ассистента
Дата: {date.today().strftime('%d.%m.%Y')}

## 1. О бизнесе и задаче
[подробно]

## 2. Кто будет пользоваться
[подробно]

## 3. Что делает помощник — функции и сценарии
[подробно, с примерами диалогов]

## 4. Источники информации
[документы, сайты, базы данных]

## 5. Где работает
[Telegram, сайт, WhatsApp и т.д.]

## 6. Память и история диалогов
[что запоминает, как долго]

## 7. Ограничения
[что нельзя, секретные данные]

## 8. Сроки и бюджет
[дедлайн, бюджет, поддержка после запуска]

## 9. Дополнительные пожелания
[всё остальное]

## 10. Контактные данные клиента
[имя и способ связи]"""

TG_BOT_SYSTEM = f"""Ты помогаешь человеку описать его будущего Telegram-бота, чтобы потом разработчик Александр Прохоров мог его сделать.

Сегодняшняя дата: {date.today().strftime('%d.%m.%Y')}

## КАК ОБЩАТЬСЯ
Говори как друг — просто, тепло, без умных слов. Представь что объясняешь бабушке.
Никакого жаргона. Конкретные замены:
- не "монетизация" — а "как на этом боте можно зарабатывать"
- не "воронка" — а "как бот приводит к покупке шаг за шагом"
- не "лид-магнит" — а "что-то бесплатное что бот даёт в обмен на контакт"
- не "интеграции" — а "подключение к другим программам — например Google Таблицы, оплата, CRM"
- не "CRM" — а "программа для учёта клиентов"
- не "рассылка" — а "сообщения которые бот отправляет сам, всем или части пользователей"
Если человек не понял вопрос — переформулируй проще, без извинений.

## ЧТО НУЖНО УЗНАТЬ (8 шагов):
1. Зачем бот — что должен делать: принимать заказы, отвечать на вопросы, записывать на приём, рассылать новости?
2. Кто будет пользоваться — клиенты? сотрудники? сколько примерно человек?
3. Как работает — объясни шаг за шагом что делает бот когда человек пишет ему
4. Что пишет и откуда берёт — какие сообщения отправляет, откуда берёт информацию
5. Нужны ли другие программы — например оплата прямо в боте, Google Таблицы, учёт клиентов
6. Что узнаём о пользователях — имя, телефон, email — что нужно собирать
7. Как зарабатывать — есть ли платные функции, подписка, или бот просто помогает продавать
8. Контакт — как зовут и как связаться после

## ПРАВИЛА
- НАЧИНАЙ каждый свой ответ с маркера текущей темы: [ТЕМА:N] — например [ТЕМА:2]
- Начни с тёплого приветствия и первого вопроса про цель бота
- Один вопрос за раз — никогда не задавай несколько сразу
- Если ответ непонятный — уточни другими словами

## КОГДА ВСЕ 8 ШАГОВ ПРОЙДЕНЫ:
Напиши строго в таком формате:

[ТЕМА:8]
ТЗ_ПРОВЕРКА
Вот что я узнал о вашем боте:
• Цель: [коротко]
• Кто пользуется: [коротко]
• Как работает: [коротко]
• Что пишет: [коротко]
• Другие программы: [коротко]
• Что собираем о людях: [коротко]
• Заработок: [коротко]
• Контакт: [имя и контакт]
ТЗ_ГОТОВО
# Техническое задание на разработку Telegram-бота
Дата: {date.today().strftime('%d.%m.%Y')}

## 1. Цель и задача бота
[подробно]

## 2. Целевая аудитория
[подробно]

## 3. Функциональность и сценарии
[список команд, каждый сценарий шаг за шагом]

## 4. Контент и источники данных
[что отправляет, откуда берёт]

## 5. Интеграции
[список сервисов и что делает каждый]

## 6. Сбор и хранение данных пользователей
[поля, хранилище, политика]

## 7. Монетизация и воронка
[платные функции, рассылки, CTA]

## 8. Дополнительные пожелания
[всё остальное]

## 9. Контактные данные клиента
[имя и способ связи]"""


TG_MINIAPP_SYSTEM = f"""Ты помогаешь человеку описать его будущее Telegram Mini App — мини-приложение которое открывается прямо внутри Telegram. Потом разработчик Александр Прохоров сделает его.

Сегодняшняя дата: {date.today().strftime('%d.%m.%Y')}

## КАК ОБЩАТЬСЯ
Говори как друг — просто, тепло, без умных слов. Представь что объясняешь бабушке.
Никакого жаргона. Конкретные замены:
- не "Mini App" — а "мини-приложение которое открывается прямо в Telegram"
- не "онбординг" — а "что видит человек когда открывает приложение первый раз"
- не "каталог" — а "список услуг или товаров"
- не "фильтрация" — а "поиск и сортировка по категориям"
- не "Telegram Pay" — а "оплата прямо в Telegram не выходя из чата"
- не "backend" и "API" — а "программа которая хранит данные и отвечает на запросы"
- не "UI/UX" — а "как выглядит и как удобно пользоваться"
Если человек не понял вопрос — переформулируй проще, без извинений.

## ЧТО НУЖНО УЗНАТЬ (8 шагов):
1. Что должно делать — каталог услуг с записью? магазин? витрина? голосование? что-то другое?
2. Кто будет открывать — клиенты? подписчики канала? как они найдут приложение (кнопка в боте, ссылка в канале, QR-код)?
3. Какие экраны нужны — что видит человек: главная, список услуг, карточка, корзина, запись, личный кабинет?
4. Нужна ли запись или покупка — может ли человек записаться или купить прямо внутри, нужна ли оплата в Telegram?
5. Какой контент — что показываем: услуги с ценами, товары, расписание, портфолио — что уже есть, что нужно заполнить?
6. Как должно выглядеть — цвета, стиль, есть ли логотип, примеры которые нравятся (сайт, бот или приложение)?
7. Что происходит после — после записи или покупки: приходит уведомление в Telegram? напоминание перед визитом? что-то ещё?
8. Контакт — как зовут и как связаться после

## ПРАВИЛА
- НАЧИНАЙ каждый свой ответ с маркера текущей темы: [ТЕМА:N] — например [ТЕМА:3]
- Начни с тёплого приветствия и первого вопроса про цель приложения
- Один вопрос за раз — никогда не задавай несколько сразу
- Если ответ непонятный — уточни другими словами

## КОГДА ВСЕ 8 ШАГОВ ПРОЙДЕНЫ:
Напиши строго в таком формате:

[ТЕМА:8]
ТЗ_ПРОВЕРКА
Вот что я узнал о вашем мини-приложении:
• Что делает: [коротко]
• Кто пользуется: [коротко]
• Экраны: [коротко]
• Запись и оплата: [коротко]
• Контент: [коротко]
• Внешний вид: [коротко]
• После действия: [коротко]
• Контакт: [имя и контакт]
ТЗ_ГОТОВО
# Техническое задание на разработку Telegram Mini App
Дата: {date.today().strftime('%d.%m.%Y')}

## 1. Цель и задача приложения
[подробно — что делает, какую проблему решает]

## 2. Целевая аудитория
[кто пользуется, как находит приложение]

## 3. Экраны и пользовательский путь
[список экранов с описанием — что видит пользователь на каждом шаге]

## 4. Запись, заказ и оплата
[нужна ли онлайн-запись, корзина, оплата через Telegram Pay, предоплата]

## 5. Контент и данные
[что показываем, сколько позиций, откуда берутся данные, что нужно подготовить]

## 6. Внешний вид и стиль
[цвета, фирменный стиль, примеры, ощущение которое должно быть]

## 7. Уведомления и автоматизация
[что происходит после записи/покупки, напоминания, подтверждения]

## 8. Дополнительные пожелания
[всё остальное]

## 9. Контактные данные клиента
[имя и способ связи]"""


def build_system(site_type: str) -> str:
    if site_type == "ai_agent":
        return AI_AGENT_SYSTEM
    if site_type == "tg_bot":
        return TG_BOT_SYSTEM
    if site_type == "tg_miniapp":
        return TG_MINIAPP_SYSTEM
    hint = SITE_TYPE_HINTS.get(site_type, "")
    return f"{BASE_SYSTEM}\n\n## ТИП САЙТА\n{hint}"


def progress_text(n: int, site_type: str = "") -> str:
    if site_type == "ai_agent":
        name = TOPIC_NAMES_AI.get(n, "")
    elif site_type == "tg_bot":
        name = TOPIC_NAMES_TG.get(n, "")
    elif site_type == "tg_miniapp":
        name = TOPIC_NAMES_MINIAPP.get(n, "")
    else:
        name = TOPIC_NAMES.get(n, "")
    done = "●" * n
    todo = "○" * (8 - n)
    return f"📍 Тема {n}/8 — {name}\n{done}{todo}"


# ─── KEYBOARDS ────────────────────────────────────────────────────────────────

def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(SITE_TYPES["landing"],   callback_data="type_landing"),
         InlineKeyboardButton(SITE_TYPES["shop"],      callback_data="type_shop")],
        [InlineKeyboardButton(SITE_TYPES["corporate"], callback_data="type_corporate"),
         InlineKeyboardButton(SITE_TYPES["portfolio"], callback_data="type_portfolio")],
        [InlineKeyboardButton(SITE_TYPES["vizitka"],   callback_data="type_vizitka"),
         InlineKeyboardButton(SITE_TYPES["other"],     callback_data="type_other")],
        [InlineKeyboardButton(SITE_TYPES["ai_agent"],   callback_data="type_ai_agent"),
         InlineKeyboardButton(SITE_TYPES["tg_bot"],     callback_data="type_tg_bot")],
        [InlineKeyboardButton(SITE_TYPES["tg_miniapp"], callback_data="type_tg_miniapp")],
    ])


def nav_keyboard(step_count: int) -> InlineKeyboardMarkup | None:
    buttons = []
    if step_count > 0:
        buttons.append([InlineKeyboardButton("◀️ Предыдущий вопрос", callback_data="go_back")])
    if step_count > 1:
        buttons.append([InlineKeyboardButton("✏️ Изменить любой ответ", callback_data="edit_menu")])
    return InlineKeyboardMarkup(buttons) if buttons else None


def steps_keyboard(steps: list) -> InlineKeyboardMarkup:
    buttons = []
    show = steps[-8:] if len(steps) > 8 else steps
    offset = len(steps) - len(show)
    for i, step in enumerate(show):
        real_idx = offset + i
        q = step["question"].replace("\n", " ")
        label = (q[:38] + "…") if len(q) > 38 else q
        buttons.append([InlineKeyboardButton(f"{real_idx + 1}. {label}", callback_data=f"edit_{real_idx}")])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="edit_cancel")])
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Всё верно, создать ТЗ", callback_data="confirm_tz"),
        InlineKeyboardButton("✏️ Дополнить", callback_data="reject_tz"),
    ]])


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Согласен", callback_data="consent_yes"),
        InlineKeyboardButton("❌ Отказаться", callback_data="consent_no"),
    ]])


# ─── URL ENRICHMENT ───────────────────────────────────────────────────────────

def fetch_url_info(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        r    = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title")
        desc  = soup.find("meta", attrs={"name": "description"})
        info  = f"[Сайт: {url}"
        if title:
            info += f" | {title.get_text(strip=True)}"
        if desc and desc.get("content"):
            info += f" — {desc['content'][:200]}"
        return info + "]"
    except Exception as e:
        logger.warning(f"fetch_url_info {url}: {e}")
        return f"[Ссылка: {url}]"


# ─── CLAUDE ───────────────────────────────────────────────────────────────────

def build_messages(type_label: str, first_msg: str, steps: list, user_content) -> list:
    msgs = [
        {"role": "user",      "content": f"Я хочу {type_label}"},
        {"role": "assistant", "content": first_msg},
    ]
    for step in steps:
        msgs.append({"role": "user",      "content": step["user"]})
        msgs.append({"role": "assistant", "content": step["bot"]})
    msgs.append({"role": "user", "content": user_content})
    return msgs


def _to_openai_content(content):
    """Контент Anthropic (строка или список блоков) → формат OpenAI/OpenRouter."""
    if isinstance(content, str):
        return content
    out = []
    for block in content:
        if block["type"] == "text":
            out.append({"type": "text", "text": block["text"]})
        elif block["type"] == "image":
            src = block["source"]
            out.append({
                "type": "image_url",
                "image_url": {"url": f"data:{src['media_type']};base64,{src['data']}"},
            })
    return out


def call_claude_sync(system: str, messages: list, max_tokens: int = 800) -> str:
    oai_messages = [{"role": "system", "content": system}]
    for m in messages:
        oai_messages.append({"role": m["role"], "content": _to_openai_content(m["content"])})
    resp = llm.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=max_tokens,
        messages=oai_messages,
    )
    return resp.choices[0].message.content


# ─── TZ SENDER ────────────────────────────────────────────────────────────────

async def _send_tz(message, context, session: dict, tz_text: str):
    type_label = SITE_TYPES.get(session["site_type"], "Сайт")
    chat_id    = message.chat_id

    filename_map = {
        "ai_agent":   "ТЗ_на_ИИ_ассистента.txt",
        "tg_bot":     "ТЗ_на_Telegram_бот.txt",
        "tg_miniapp": "ТЗ_на_Telegram_Mini_App.txt",
    }
    tz_filename = filename_map.get(session["site_type"], "ТЗ_на_сайт.txt")
    bio = BytesIO(tz_text.encode("utf-8"))
    await message.reply_document(
        document=bio,
        filename=tz_filename,
        caption=(
            f"✅ Ваше ТЗ на *{type_label}* готово!\n\n"
            "Передайте файл Александру или напишите ему:\n"
            "👉 @alex\\_prohar"
        ),
        parse_mode="Markdown",
    )

    chat      = await context.bot.get_chat(chat_id)
    username  = f"@{chat.username}" if chat.username else "без username"
    full_name = chat.full_name or "Клиент"

    contact_hint = ""
    if "Контактные данные клиента" in tz_text:
        part = tz_text.split("Контактные данные клиента", 1)[1][:150].strip()
        contact_hint = f"\nКонтакт: {part}"

    await context.bot.send_message(
        chat_id=ALEXANDER_CHAT_ID,
        text=(
            f"🔔 Новая заявка с ТЗ!\n\n"
            f"От: {full_name} ({username})\n"
            f"Тип: {type_label}"
            f"{contact_hint}\n\n"
            f"Превью:\n{tz_text[:500]}..."
        ),
    )
    bio2 = BytesIO(tz_text.encode("utf-8"))
    await context.bot.send_document(
        chat_id=ALEXANDER_CHAT_ID,
        document=bio2,
        filename=f"ТЗ_{full_name}.txt",
    )
    db_delete(chat_id)


# ─── CORE PROCESS ─────────────────────────────────────────────────────────────

FINISH_TRIGGER = (
    "Я ответил на все вопросы. Пожалуйста, подведи итог и составь полное ТЗ прямо сейчас. "
    "Строго следуй формату: сначала ТЗ_ПРОВЕРКА с кратким резюме, затем ТЗ_ГОТОВО с полным ТЗ."
)


async def _process(update: Update, context: ContextTypes.DEFAULT_TYPE,
                   session: dict, user_content, user_label: str):
    type_label = SITE_TYPES.get(session["site_type"], "Сайт")
    system     = build_system(session["site_type"])

    # Auto-inject finish trigger after 10+ steps so Claude doesn't loop forever
    steps_count = len(session["steps"])
    if steps_count >= 10 and isinstance(user_content, str):
        user_content = user_content + "\n\n" + FINISH_TRIGGER

    messages   = build_messages(type_label, session["first_msg"], session["steps"], user_content)
    chat_id    = update.effective_chat.id

    try:
        max_tokens = 4096 if steps_count >= 7 else 2000
        reply = await asyncio.to_thread(call_claude_sync, system, messages, max_tokens)
    except Exception as e:
        logger.error(f"Claude error: {e}", exc_info=True)
        try:
            await update.message.reply_text("❌ Ошибка. Попробуй ещё раз или напиши /reset")
        except Exception:
            pass
        return

    # Extract and strip topic marker
    m         = TOPIC_RE.search(reply)
    topic_num = int(m.group(1)) if m else None
    clean     = TOPIC_RE.sub("", reply).strip()

    # ── Confirmation stage ──────────────────────────────────────────────────
    if "ТЗ_ПРОВЕРКА" in clean:
        after = clean.split("ТЗ_ПРОВЕРКА", 1)[1].strip()
        if "ТЗ_ГОТОВО" in after:
            summary, tz_text = after.split("ТЗ_ГОТОВО", 1)
            summary  = summary.strip()
            tz_text  = tz_text.strip()

            new_step  = {"question": session["cur_q"], "user": user_label, "bot": clean}
            new_steps = session["steps"] + [new_step]
            db_save(chat_id,
                    site_type=session["site_type"],
                    first_msg=session["first_msg"],
                    steps=new_steps,
                    cur_q=clean,
                    pending_tz=tz_text)

            await update.message.reply_text(
                f"📋 *Проверьте собранную информацию:*\n\n{summary}\n\n"
                "Всё верно или хотите что-то дополнить?",
                parse_mode="Markdown",
                reply_markup=confirm_keyboard(),
            )
            return

    # ── Direct TZ (fallback without ПРОВЕРКА) ──────────────────────────────
    if "ТЗ_ГОТОВО" in clean:
        tz_text = clean.split("ТЗ_ГОТОВО", 1)[1].strip()
        await update.message.reply_text("✅ Формирую ТЗ... ⏳")
        await _send_tz(update.message, context, session, tz_text)
        return

    # ── Normal question flow ────────────────────────────────────────────────
    if topic_num:
        await update.message.reply_text(progress_text(topic_num, session["site_type"]))

    new_step  = {"question": session["cur_q"], "user": user_label, "bot": clean}
    new_steps = session["steps"] + [new_step]
    db_save(chat_id,
            site_type=session["site_type"],
            first_msg=session["first_msg"],
            steps=new_steps,
            cur_q=clean)

    await update.message.reply_text(clean, reply_markup=nav_keyboard(len(new_steps)))


def _no_session_reply(context: ContextTypes.DEFAULT_TYPE) -> dict:
    site_type = context.user_data.get("site_type")
    if site_type:
        label = SITE_TYPES.get(site_type, "Сайт")
        return {
            "text": (
                f"⚠️ Сессия прервалась — бот перезапускался.\n\n"
                f"Вы выбирали: *{label}*\n\nНачнём заново 👇"
            ),
            "parse_mode": "Markdown",
            "reply_markup": start_keyboard(),
        }
    return {"text": "👋 Нажмите /start чтобы начать составление ТЗ.", "reply_markup": start_keyboard()}


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_delete(update.effective_chat.id)
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Я помогу составить техническое задание на ваш сайт.\n\n"
        "В процессе интервью я запрошу ваше имя и контакт для обратной связи.\n\n"
        "📄 Нажимая «Согласен», вы подтверждаете согласие на обработку персональных данных "
        "в соответствии с [Политикой конфиденциальности](https://prohar2f-pixel.github.io/my-first-project/privacy.html).",
        parse_mode="Markdown",
        reply_markup=consent_keyboard(),
        disable_web_page_preview=True,
    )


async def handle_consent_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✅ Спасибо!\n\n*Что вы хотите создать?*",
        parse_mode="Markdown",
        reply_markup=start_keyboard(),
    )


async def handle_consent_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Понял. Без согласия на обработку данных я не могу начать интервью.\n\n"
        "Если передумаете — нажмите /start"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_delete(update.effective_chat.id)
    context.user_data.clear()
    await update.message.reply_text("🔄 Начинаем заново!", reply_markup=start_keyboard())


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session or not session["steps"]:
        await update.message.reply_text("Нет активной сессии или ещё не начали. Нажмите /start")
        return
    await update.message.reply_text("⏳ Собираю ТЗ по всем вашим ответам...")
    await _process(update, context, session, FINISH_TRIGGER, "[Завершить интервью]")


async def handle_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query      = update.callback_query
    await query.answer()
    site_type  = query.data.replace("type_", "")
    chat_id    = query.message.chat_id
    type_label = SITE_TYPES.get(site_type, "Сайт")

    context.user_data["site_type"] = site_type
    await query.edit_message_text(f"Отлично, выбрано: *{type_label}*\n\nНачинаем! ⏳", parse_mode="Markdown")

    system = build_system(site_type)
    try:
        first_msg = await asyncio.to_thread(
            call_claude_sync, system,
            [{"role": "user", "content": f"Я хочу {type_label}"}], 600
        )
        clean_first = TOPIC_RE.sub("", first_msg).strip()
        db_save(chat_id, site_type=site_type, first_msg=clean_first, steps=[], cur_q=clean_first)
        await query.message.reply_text(clean_first)
    except Exception as e:
        logger.error(f"handle_type_callback: {e}", exc_info=True)
        error_text = f"❌ Ошибка: {str(e)[:100]}\n\nПопробуй /start или напиши @alex_prohar"
        await query.message.reply_text(error_text)


async def handle_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    session = db_get(chat_id)
    if not session or not session["steps"]:
        await query.message.reply_text("↩️ Уже в самом начале — вернуться некуда.")
        return

    last_step = session["steps"][-1]
    new_steps = session["steps"][:-1]
    db_save(chat_id,
            site_type=session["site_type"],
            first_msg=session["first_msg"],
            steps=new_steps,
            cur_q=last_step["question"])

    await query.message.reply_text(
        f"↩️ Вернулись к вопросу:\n\n{last_step['question']}",
        reply_markup=nav_keyboard(len(new_steps)),
    )


async def handle_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    session = db_get(chat_id)
    if not session or not session["steps"]:
        await query.message.reply_text("Нечего редактировать.")
        return

    await query.message.reply_text(
        "Выберите вопрос, ответ на который хотите изменить:",
        reply_markup=steps_keyboard(session["steps"]),
    )


async def handle_edit_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query    = update.callback_query
    await query.answer()
    chat_id  = query.message.chat_id
    step_idx = int(query.data.replace("edit_", ""))

    session = db_get(chat_id)
    if not session or step_idx >= len(session["steps"]):
        await query.message.reply_text("❌ Шаг не найден.")
        return

    target_q  = session["steps"][step_idx]["question"]
    new_steps = session["steps"][:step_idx]

    db_save(chat_id,
            site_type=session["site_type"],
            first_msg=session["first_msg"],
            steps=new_steps,
            cur_q=target_q)

    await query.edit_message_text(
        f"✏️ Возвращаемся к вопросу:\n\n{target_q}",
        reply_markup=nav_keyboard(len(new_steps)),
    )


async def handle_edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        await query.delete_message()
    except Exception:
        await query.edit_message_text("❌ Отменено.")


async def handle_confirm_tz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    session = db_get(chat_id)
    if not session or not session.get("pending_tz"):
        await query.message.reply_text("❌ ТЗ не найдено. Напиши /start")
        return

    await query.edit_message_text("✅ Отлично! Формирую ТЗ... ⏳")
    await _send_tz(query.message, context, session, session["pending_tz"])


async def handle_reject_tz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Хорошо! ✏️ Напишите что хотите уточнить или добавить — продолжим интервью."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)

    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    user_text = update.message.text
    urls      = URL_RE.findall(user_text)
    if urls:
        await update.message.reply_text("🔗 Смотрю ссылку... ⏳")
        url_infos = await asyncio.gather(*[asyncio.to_thread(fetch_url_info, u) for u in urls])
        enriched  = user_text + "\n\n" + "\n".join(url_infos)
    else:
        enriched = user_text

    await _process(update, context, session, enriched, user_text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    await update.message.reply_text("📸 Анализирую изображение... ⏳")
    photo   = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    buf     = BytesIO()
    await tg_file.download_to_memory(buf)
    img_b64 = base64.standard_b64encode(buf.getvalue()).decode()
    caption = update.message.caption or ""
    label   = f"[📸 Изображение]{' — ' + caption if caption else ''}"

    user_content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
        {"type": "text",  "text": f"Визуальный референс.{' ' + caption if caption else ''} Проанализируй стиль и продолжи интервью."},
    ]
    await _process(update, context, session, user_content, label)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    doc  = update.message.document
    mime = doc.mime_type or ""

    if "pdf" in mime:
        await update.message.reply_text("📄 Читаю документ... ⏳")
        tg_file = await context.bot.get_file(doc.file_id)
        buf     = BytesIO()
        await tg_file.download_to_memory(buf)

        def extract_pdf(data: bytes) -> str:
            import pdfplumber
            texts = []
            with pdfplumber.open(BytesIO(data)) as pdf:
                for page in pdf.pages[:10]:
                    t = page.extract_text() or ""
                    if t:
                        texts.append(t)
                    page.flush_cache()
            return "\n".join(texts)[:3000]

        try:
            pdf_text = await asyncio.to_thread(extract_pdf, buf.getvalue())
        except Exception as e:
            logger.error(f"PDF extract: {e}")
            await update.message.reply_text("❌ Не удалось прочитать PDF. Опишите текстом.")
            return

        label = f"[📄 PDF: {doc.file_name}]"
        await _process(update, context, session, f"{label}\n\n{pdf_text}", label)

    elif mime.startswith("image/"):
        await update.message.reply_text("📸 Анализирую изображение... ⏳")
        tg_file = await context.bot.get_file(doc.file_id)
        buf     = BytesIO()
        await tg_file.download_to_memory(buf)
        img_b64 = base64.standard_b64encode(buf.getvalue()).decode()
        caption = update.message.caption or ""
        label   = f"[📸 Изображение (файл)]{' — ' + caption if caption else ''}"
        user_content = [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
            {"type": "text",  "text": f"Визуальный референс.{' ' + caption if caption else ''} Проанализируй стиль и продолжи интервью."},
        ]
        await _process(update, context, session, user_content, label)

    else:
        await update.message.reply_text(
            f"📎 Файл *{doc.file_name}* получен, но я умею читать только PDF и изображения.\n\n"
            "Пришлите скриншот или ссылку — или опишите текстом.",
            parse_mode="Markdown",
        )


async def _transcribe_and_reply(update: Update, data: bytes,
                                filename: str, emoji: str) -> str | None:
    """Распознаёт аудио, показывает текст пользователю (без Markdown, кусками).
    Возвращает текст или None, если распознать не удалось (пользователю уже ответили)."""
    try:
        text = await asyncio.to_thread(asr.transcribe, data, filename)
    except asr.RateLimited:
        await update.message.reply_text(
            "⏳ Слишком много запросов — подождите минуту и отправьте ещё раз, "
            "или напишите текстом."
        )
        return None
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Не удалось распознать — попробуйте ещё раз или напишите текстом."
        )
        return None

    if not text:
        await update.message.reply_text(
            "🤔 Не расслышал — повторите, пожалуйста, или напишите текстом."
        )
        return None

    # без parse_mode: в сыром транскрипте могут быть _ и *, ломающие Markdown
    for chunk in asr.split_for_telegram(f"{emoji} «{text}»"):
        await update.message.reply_text(chunk)
    return text


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    voice = update.message.voice
    if voice.duration and voice.duration > 600:
        await update.message.reply_text(
            "⏱ Запись длиннее 10 минут — расскажите короче или напишите текстом."
        )
        return

    await update.message.reply_text("🎤 Распознаю голос... ⏳")
    tg_file = await context.bot.get_file(voice.file_id)
    buf     = BytesIO()
    await tg_file.download_to_memory(buf)

    text = await _transcribe_and_reply(update, buf.getvalue(), "voice.ogg", "🎤")
    if text:
        await _process(update, context, session, text, f"[🎤 Голосовое] {text}")


async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    await update.message.reply_text("🎥 Распознаю кружочек... ⏳")
    note    = update.message.video_note
    tg_file = await context.bot.get_file(note.file_id)
    buf     = BytesIO()
    await tg_file.download_to_memory(buf)

    text = await _transcribe_and_reply(update, buf.getvalue(), "note.mp4", "📹")
    if text:
        await _process(update, context, session, text, f"[📹 Кружочек] {text}")


async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if session:
        await update.message.reply_text(
            "📝 Я понимаю текст, голосовые, кружочки, изображения, PDF и ссылки.\n"
            "Напишите ответ, запишите голосовое или пришлите скриншот / файл."
        )
    else:
        await update.message.reply_text(**_no_session_reply(context))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if isinstance(error, Conflict):
        logger.error(f"⚠️  Conflict error — another bot instance is running. Waiting before retry... {error}")
        await asyncio.sleep(5)
    else:
        logger.error("Exception while handling update:", exc_info=error)


async def post_init(app: Application) -> None:
    db_init()

    logger.info("🔄 Очищаю webhook состояние...")
    try:
        # Убедиться что нет webhook'а
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удалён, pending updates очищены")
    except Exception as e:
        logger.warning(f"⚠️  Ошибка при удалении webhook: {e}")

    # Подождать чтобы Telegram обработал удаление
    await asyncio.sleep(2)

    # Попытаться получить обновления чтобы очистить очередь
    try:
        logger.info("🔄 Очищаю очередь обновлений...")
        updates = await app.bot.get_updates(timeout=1, read_timeout=2)
        if updates:
            logger.info(f"✅ Очищено {len(updates)} pending обновлений")
    except Exception as e:
        logger.warning(f"⚠️  Ошибка при очистке очереди: {e}")

    await asyncio.sleep(1)
    await app.bot.set_my_commands([
        BotCommand("start",  "Начать сбор ТЗ"),
        BotCommand("finish", "Завершить интервью и получить ТЗ"),
        BotCommand("reset",  "Начать заново"),
    ])
    logger.info("✅ Bot ready!")


async def main_async() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("reset",  reset))
    app.add_handler(CommandHandler("finish", finish))

    app.add_handler(CallbackQueryHandler(handle_consent_yes,   pattern="^consent_yes$"))
    app.add_handler(CallbackQueryHandler(handle_consent_no,    pattern="^consent_no$"))
    app.add_handler(CallbackQueryHandler(handle_type_callback, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(handle_back_callback, pattern="^go_back$"))
    app.add_handler(CallbackQueryHandler(handle_edit_menu,     pattern="^edit_menu$"))
    app.add_handler(CallbackQueryHandler(handle_edit_step,     pattern=r"^edit_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_edit_cancel,   pattern="^edit_cancel$"))
    app.add_handler(CallbackQueryHandler(handle_confirm_tz,    pattern="^confirm_tz$"))
    app.add_handler(CallbackQueryHandler(handle_reject_tz,     pattern="^reject_tz$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO,        handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.VOICE,        handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE,   handle_video_note))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_other))

    app.add_error_handler(error_handler)

    def stop_signal_handler(signum, frame):
        logger.info("⏹️  Graceful shutdown signal received")
        app.stop()

    signal.signal(signal.SIGTERM, stop_signal_handler)
    signal.signal(signal.SIGINT, stop_signal_handler)

    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        try:
            logger.info(f"🚀 Запуск polling (попытка {retry_count + 1}/{max_retries})...")
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=False,
                timeout=15,
                read_timeout=15,
                connect_timeout=15,
                write_timeout=15,
            )
            break  # Успешный запуск
        except Conflict as e:
            retry_count += 1
            wait_time = 10 * (2 ** (retry_count - 1))  # Exponential backoff: 10s, 20s, 40s...
            logger.warning(f"⚠️  Conflict: {e}")
            logger.info(f"⏳ Ожидание {wait_time}с перед повтором (попытка {retry_count}/{max_retries})...")
            await asyncio.sleep(wait_time)
            if retry_count >= max_retries:
                logger.error("❌ Не удалось запустить бота после нескольких попыток")
                raise
        except KeyboardInterrupt:
            logger.info("⏹️  Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            raise


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
