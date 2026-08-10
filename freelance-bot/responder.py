from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY
from database import get_profile_fields
from response_policy import (
    DEMO_PROJECTS,
    STRICT_RESPONSE_RULES,
    VERIFIED_CAPABILITIES,
    VERIFIED_PROJECTS,
    DraftResult,
    assess_job_risks,
    build_safe_fallback,
    validate_generated_response,
)


def build_profile_text() -> str:
    f = get_profile_fields()
    services = f.get("services", "").replace(chr(0x2014), "-")
    capabilities = "\n".join(f"- {item}" for item in VERIFIED_CAPABILITIES)
    projects = "\n".join(
        f"- {item['name']}: {item['work']}. {item['url']}"
        for item in VERIFIED_PROJECTS
    )
    demos = "\n".join(
        f"- {item['name']}: концепт, не клиентская работа, публичной ссылки нет"
        for item in DEMO_PROJECTS
    )
    rules = "\n".join(f"- {rule}" for rule in STRICT_RESPONSE_RULES)
    return (
        f"Ты - {f.get('name', 'Александр')}, {f.get('title', 'фрилансер')}. "
        f"Пишешь отклик на заказ от своего имени.\n\n"
        "Ниже перечислены только подтверждённые факты. Любые сведения из "
        "старого редактируемого профиля, которых здесь нет, не подтверждены.\n\n"
        f"Подтверждённые навыки:\n{capabilities}\n\n"
        f"Подтверждённые проекты:\n{projects}\n\n"
        f"Демонстрационные концепты:\n{demos}\n\n"
        "Портфолио: https://aiprohar.ru/\n"
        "Контакт: @alex_prohar в Telegram\n\n"
        f"Ориентиры услуг, не являющиеся точной оценкой заказа:\n{services}\n\n"
        f"Стиль откликов: {f.get('style', 'Коротко, по делу, без воды.')}\n\n"
        f"Обязательные правила:\n{rules}"
    )


def _draft_prompt(
    job_title: str,
    job_description: str,
    source: str,
    risks: tuple[str, ...],
) -> str:
    risk_text = ", ".join(risks) if risks else "нет выявленных рисков"
    return (
        f"Заказ с {source}:\n"
        f"Заголовок: {job_title}\n"
        f"Описание: {job_description}\n\n"
        f"Риски проверки: {risk_text}.\n\n"
        "Напиши короткий персональный черновик отклика из 3-5 предложений. "
        "Покажи, что понял задачу, и используй только подтверждённые факты. "
        "Если объём неполный, не называй точную цену и срок. "
        "Если требуется неподтверждённая платформа, честно обозначь границу "
        "и предложи собственный код только как альтернативу. "
        "Заканчивай понятным следующим шагом."
    )


def _completion_text(completion) -> str:
    text = completion.choices[0].message.content
    return text.strip() if isinstance(text, str) else ""


async def generate_draft(
    job_title: str,
    job_description: str,
    source: str,
) -> DraftResult:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY не задан в .env файле")

    risks = assess_job_risks(job_title, job_description)
    profile = build_profile_text()
    prompt = _draft_prompt(job_title, job_description, source, risks)

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    first_completion = await client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        max_tokens=500,
        messages=[
            {"role": "system", "content": profile},
            {"role": "user", "content": prompt},
        ],
    )
    first_text = _completion_text(first_completion)
    first_violations = validate_generated_response(first_text, risks)
    if first_text and not first_violations:
        return DraftResult(text=first_text, warnings=risks)

    correction = (
        f"Перепиши черновик. Нарушения проверки: "
        f"{', '.join(first_violations) if first_violations else 'пустой ответ'}. "
        "Удали неподтверждённые утверждения, точные обещания и неизвестные ссылки."
    )
    second_completion = await client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        max_tokens=500,
        messages=[
            {"role": "system", "content": profile},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": first_text},
            {"role": "user", "content": correction},
        ],
    )
    second_text = _completion_text(second_completion)
    second_violations = validate_generated_response(second_text, risks)
    if second_text and not second_violations:
        return DraftResult(
            text=second_text,
            warnings=risks,
            regenerated=True,
        )

    return build_safe_fallback(risks, job_title, job_description)


async def generate_response(job_title: str, job_description: str, source: str) -> str:
    """Compatibility wrapper for current Telegram handlers."""
    result = await generate_draft(job_title, job_description, source)
    return result.text
