from collections.abc import Awaitable, Callable
from html import escape

from response_policy import DraftResult


DraftGenerator = Callable[[str, str, str], Awaitable[DraftResult]]

PLATFORM_NAMES = {
    "tilda": "Tilda",
    "wordpress": "WordPress",
    "wix": "Wix",
    "webflow": "Webflow",
}

RISK_MESSAGES = {
    "missing_scope:layouts": "Не проверены макеты или ссылка на них.",
    "missing_scope:unique_pages": "Неизвестно количество уникальных страниц.",
    "missing_scope:integrations": "Не уточнены формы и интеграции.",
    "exact_estimate:unsafe": "Точную цену и срок нужно подтвердить после уточнения объёма.",
}


def _risk_message(risk: str) -> str:
    prefix = "unverified_platform:"
    if risk.startswith(prefix):
        slug = risk.removeprefix(prefix)
        platform = PLATFORM_NAMES.get(slug, slug.capitalize())
        return (
            f"Нет подтверждённого коммерческого опыта на платформе {platform}."
        )
    return RISK_MESSAGES.get(
        risk,
        "Проверьте факты и формулировки перед отправкой.",
    )


def format_draft_message(result: DraftResult) -> str:
    checks: list[str] = []
    if result.fallback:
        checks.append("Использован безопасный шаблон после двух отклонённых вариантов.")
    elif result.regenerated:
        checks.append("Первый вариант был автоматически исправлен политикой безопасности.")

    checks.extend(_risk_message(risk) for risk in result.warnings)
    if not checks:
        checks.append("Автоматических предупреждений нет, но факты всё равно нужно проверить.")

    checklist = "\n".join(f"• {escape(item)}" for item in checks)
    return (
        "✍️ <b>Черновик отклика</b>\n\n"
        f"{escape(result.text)}\n\n"
        "⚠️ <b>Проверить перед отправкой</b>\n"
        f"{checklist}\n\n"
        "📌 Черновик не отправлен заказчику. Скопируйте его только после ручной проверки."
    )


def format_generation_error(error: Exception) -> str:
    del error
    return (
        "❌ <b>Не удалось подготовить безопасный черновик.</b>\n\n"
        "Повторите попытку позже или уточните факты о задаче вручную. "
        "Отклонённый текст не показан."
    )


async def generate_formatted_draft(
    job_title: str,
    job_description: str,
    source: str,
    generator: DraftGenerator,
) -> str:
    result = await generator(job_title, job_description, source)
    return format_draft_message(result)
