from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
USER_ID = int(os.getenv("USER_ID", "0"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Telegram API credentials for reading channels (get at my.telegram.org)
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

# Telegram channels to monitor, comma-separated
DEFAULT_TG_CHANNELS = (
    "@freelansim_ru,"    # Habr Freelance — заказы с ценами на боты, Python, WordPress, сайты
    "@freelance_ru,"     # FL.ru — общий фриланс, крупнейший русскоязычный канал
    "@web_fl,"           # Фрилансер — заказы на верстку, WordPress, лендинги
    "@workk_on,"         # Work On — проекты на лендинги, веб-дизайн (72k подписчиков)
    "@allgigs,"          # Mellow — международные заказы, веб, дизайн, разработка
    "@toppchallenge,"    # Топп — заказы и проекты для разработчиков
    "@webfrl,"           # Веб-фриланс — лендинги, вёрстка, веб-разработка
    "@zakaz_design,"     # Заказы на дизайн и разработку от заказчиков
    "@designer_ru,"      # Ищу дизайнера — живые заказчики ищут специалистов
    "@workinart,"        # Дизайн + веб-работа
    "@kadrof_work,"      # Kadrof — проверенные вакансии и заказы
    "@zapwork,"          # Удалёнщики — удалённая работа и фриланс
    "@dnative_job,"      # Digital-вакансии — SMM, веб, digital-маркетинг
    "@freelance_all,"    # Все фриланс-заказы — агрегатор из разных площадок
    "@youdo_ru,"         # YouDo — бытовые и digital-задачи
    "@freelance_habr,"   # Хабр Фриланс — IT-заказы
    "@tg_jobs,"          # TG Jobs — удалённая работа и фриланс
    "@remotejob_ru,"     # Удалённая работа Россия
    "@dev_jobs_ru"       # Вакансии для разработчиков
)
TG_CHANNELS = [ch.strip() for ch in os.getenv("TG_CHANNELS", DEFAULT_TG_CHANNELS).split(",") if ch.strip()]

# How often to check platforms (seconds)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

KEYWORDS = [
    # Сайты и лендинги
    "лендинг", "landing page", "сайт-визитка", "одностраничный сайт",
    "html верстка", "верстка по макету", "tilda", "сайт на тильда",
    "тильда", "сделать сайт", "создать сайт", "разработать сайт",
    "wordpress", "вордпресс", "wp сайт",
    # Интернет-магазины
    "интернет-магазин", "интернет магазин", "магазин на сайте",
    "каталог товаров", "корзина", "woocommerce", "сайт для продаж",
    "онлайн магазин",
    # Боты и автоматизация
    "телеграм бот", "telegram bot", "тг бот", "бот для бизнеса",
    "автоматизация", "парсер", "скрипт python", "python скрипт",
    "написать бота", "создать бота", "разработать бота",
    "aiogram", "python telegram",
    # Верстка
    "сверстать", "верстальщик", "верстка сайта", "html css",
    "figma верстка", "макет верстка",
]
