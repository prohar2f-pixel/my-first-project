import anthropic
from config import ANTHROPIC_API_KEY

PROFILE = """
Ты — Александр Прохоров, фрилансер из Латвии. Пишешь отклик на заказ от своего имени.

Твои услуги и опыт:
- Сайты под ключ: визитки (от 30 000 ₽, 5-7 дней), лендинги (от 50 000 ₽, 7-14 дней), корпоративные сайты (от 90 000 ₽, 14-30 дней)
- Интернет-магазины: от 150 000 ₽, от 30 дней
- Telegram-боты и автоматизация
- Нейросети для бизнеса
- HTML/CSS верстка, WordPress, адаптивный дизайн

Контакт: @alex_prohar в Telegram
ТЗ-бот: @prohar_tz_bot
Портфолио: https://prohar2f-pixel.github.io/my-first-project/

Стиль: коротко, по делу, без воды. Никаких шаблонных фраз типа "готов рассмотреть".
Сразу показываешь что понял задачу и что конкретно можешь сделать.
"""

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def generate_response(job_title: str, job_description: str, source: str) -> str:
    prompt = f"""Заказ с {source}:
Заголовок: {job_title}
Описание: {job_description}

Напиши короткий персональный отклик (3-5 предложений).
Покажи что понял задачу, кратко расскажи почему подходишь, назови примерные сроки и стоимость если можешь оценить.
Заканчивай предложением написать в личку для деталей."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[
            {"role": "user", "content": prompt}
        ],
        system=PROFILE,
    )
    return message.content[0].text
