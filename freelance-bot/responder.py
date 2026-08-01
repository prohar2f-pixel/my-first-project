import asyncio
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY
from database import get_profile_fields


def build_profile_text() -> str:
    f = get_profile_fields()
    return (
        f"Ты — {f.get('name', 'Александр')}, {f.get('title', 'фрилансер')} из {f.get('location', 'Латвии')}. "
        f"Пишешь отклик на заказ от своего имени.\n\n"
        f"Услуги и цены:\n{f.get('services', '')}\n\n"
        f"Навыки и стек:\n{f.get('skills', '')}\n\n"
        f"Контакт: {f.get('contact', '')} в Telegram\n"
        f"ТЗ-бот: {f.get('tzbot', '')}\n"
        f"Портфолио: {f.get('portfolio', '')}\n\n"
        f"Стиль откликов: {f.get('style', 'Коротко, по делу, без воды.')}"
    )


async def generate_response(job_title: str, job_description: str, source: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY не задан в .env файле")

    profile = build_profile_text()
    prompt = (
        f"Заказ с {source}:\n"
        f"Заголовок: {job_title}\n"
        f"Описание: {job_description}\n\n"
        "Напиши короткий персональный отклик (3-5 предложений). "
        "Покажи что понял задачу, кратко расскажи почему подходишь, "
        "назови примерные сроки и стоимость если можешь оценить. "
        "Заканчивай предложением написать в личку для деталей."
    )

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    message = await client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        max_tokens=500,
        messages=[
            {"role": "system", "content": profile},
            {"role": "user", "content": prompt},
        ],
    )
    return message.choices[0].message.content
