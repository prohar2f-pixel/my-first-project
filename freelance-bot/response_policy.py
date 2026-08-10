import re
from dataclasses import dataclass
from urllib.parse import urlparse


VERIFIED_CAPABILITIES = (
    "Разработка адаптивных сайтов собственным кодом",
    "HTML, CSS и JavaScript",
    "Работа по макетам Figma",
    "Telegram-боты и AI-интеграции",
)

VERIFIED_PROJECTS = (
    {
        "name": "AiProhar",
        "url": "https://aiprohar.ru/",
        "work": "публичный сайт и портфолио на собственном коде",
    },
    {
        "name": "Недвижимость Донецк",
        "url": "https://nedvizhimostdoneck.ru/",
        "work": "веб-приложение на собственном коде с каталогом и админ-частью",
    },
)

DEMO_PROJECTS = (
    {
        "name": "SALON 01",
        "kind": "concept",
        "is_client_work": False,
        "public_url": None,
    },
)

ALLOWED_LINKS = (
    "https://aiprohar.ru/",
    "https://nedvizhimostdoneck.ru/",
    "https://t.me/alex_prohar",
)

STRICT_RESPONSE_RULES = (
    "Не придумывай опыт, проекты, клиентов, технологии и обязанности.",
    "Не называй концептуальную работу клиентским или коммерческим проектом.",
    "Не заявляй опыт Tilda, WordPress или другой платформы без подтверждения.",
    "Не придумывай измеримые результаты, проценты, цены и сроки.",
    "При неполном ТЗ проси макеты, число уникальных страниц и интеграции.",
    "Используй только подтверждённые ссылки из профиля.",
)

PLATFORM_PATTERNS = {
    "tilda": ("tilda", "тильд", "zero block", "zeroblock"),
    "wordpress": ("wordpress", "вордпресс", "elementor", "woocommerce"),
    "wix": ("wix",),
    "webflow": ("webflow",),
}


@dataclass(frozen=True)
class DraftResult:
    text: str
    warnings: tuple[str, ...] = ()
    regenerated: bool = False
    fallback: bool = False


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def assess_job_risks(job_title: str, job_description: str) -> tuple[str, ...]:
    text = f"{job_title} {job_description}".lower()
    risks: list[str] = []

    for platform, patterns in PLATFORM_PATTERNS.items():
        if _contains_any(text, patterns):
            risks.append(f"unverified_platform:{platform}")

    has_layouts = _contains_any(
        text,
        ("figma", "фигм", "макет", "дизайн-проект", "дизайн проект"),
    )
    has_unique_pages = bool(
        "уникаль" in text
        and "страниц" in text
        and re.search(
            r"\b(?:\d+|одна?|две?|три|четыре|пять|шесть|семь|восемь|девять|десять)\b",
            text,
        )
    )
    has_integrations = _contains_any(
        text,
        (
            "форма",
            "интеграц",
            "telegram",
            "телеграм",
            "api",
            "crm",
            "оплат",
            "корзин",
        ),
    )
    if not has_layouts:
        risks.append("missing_scope:layouts")
    if not has_unique_pages:
        risks.append("missing_scope:unique_pages")
    if not has_integrations:
        risks.append("missing_scope:integrations")
    if not has_layouts or not has_unique_pages or not has_integrations:
        risks.append("exact_estimate:unsafe")

    return tuple(risks)


def _extract_urls(text: str) -> tuple[str, ...]:
    urls = re.findall(r"https?://[^\s<>()\[\]]+", text, flags=re.IGNORECASE)
    return tuple(url.rstrip(".,;:!?\"") for url in urls)


def _is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username
        or parsed.password
        or port
        or parsed.query
        or parsed.fragment
    ):
        return False
    normalized = f"https://{hostname.lower()}{parsed.path}".rstrip("/")
    allowed = {item.rstrip("/") for item in ALLOWED_LINKS}
    return normalized in allowed


def _claims_platform_experience(text: str) -> bool:
    platform = r"(?:tilda|тильд\w*|wordpress|вордпресс\w*|elementor|woocommerce)"
    experience = (
        r"(?:работаю|работал|опыт|сделал|делал|разработал|поддерживал|"
        r"переносил|создал)"
    )
    positive_claim = re.search(
        rf"(?:{experience})[^.!?\n]{{0,90}}(?:{platform})|"
        rf"(?:{platform})[^.!?\n]{{0,90}}(?:{experience})",
        text,
        flags=re.IGNORECASE,
    )
    if not positive_claim:
        return False
    fragment = positive_claim.group(0).lower()
    explicitly_negative = (
        "нет подтвержд" in fragment
        or "не могу подтверд" in fragment
        or "подтверждённого" in fragment and "нет" in fragment
    )
    return not explicitly_negative


def validate_generated_response(
    text: str,
    risks: tuple[str, ...],
) -> tuple[str, ...]:
    violations: list[str] = []
    lower = text.lower()

    if _claims_platform_experience(text):
        violations.append("unsupported_claim:platform_experience")

    if "salon 01" in lower and re.search(
        r"клиент|заказчик|коммерческ|для\s+салона", lower
    ):
        violations.append("unsupported_claim:concept_as_client")

    if re.search(r"\b\d+(?:[.,]\d+)?\s*%", lower) and re.search(
        r"рост|вырос|выросла|увелич|конверси|продаж|заяв", lower
    ):
        violations.append("unsupported_claim:metric")

    if "exact_estimate:unsafe" in risks:
        commits = re.search(r"сделаю|выполню|реализую|готов\s+сделать", lower)
        exact_price = re.search(
            r"\b\d[\d\s]*(?:₽|руб(?:лей|ля|ль)?\b)", lower
        )
        exact_time = re.search(
            r"\b\d+\s*(?:дн(?:я|ей|ь)|недел(?:я|и|ь)|час(?:а|ов)?)\b",
            lower,
        )
        if commits and (exact_price or exact_time):
            violations.append("unsupported_claim:exact_estimate")

    if any(not _is_allowed_url(url) for url in _extract_urls(text)):
        violations.append("unsupported_claim:unknown_link")

    return tuple(dict.fromkeys(violations))


def build_safe_fallback(
    risks: tuple[str, ...],
    job_title: str,
    job_description: str,
) -> DraftResult:
    del job_title, job_description
    platform_risk = any(
        risk.startswith("unverified_platform:") for risk in risks
    )

    if platform_risk:
        text = (
            "Добрый день! Подтверждённого коммерческого кейса именно на этой "
            "платформе у меня сейчас нет, поэтому не буду придумывать опыт. "
            "Моя основная специализация - адаптивные сайты собственным кодом. "
            "Если вы рассматриваете перенос с сохранением контента и структуры, "
            "покажу реальные проекты. Если принципиальна работа только внутри "
            "указанной платформы, честно отмечу, что этот заказ мне не подходит. "
            "Портфолио: https://aiprohar.ru/"
        )
    else:
        text = (
            "Добрый день! Разрабатываю адаптивные сайты собственным кодом и "
            "работаю по макетам Figma. Могу показать реальные проекты и исходники. "
            "Точную стоимость и срок назову после просмотра макетов, количества "
            "уникальных страниц и интеграций, чтобы не обещать наугад. "
            "Портфолио: https://aiprohar.ru/, Telegram: @alex_prohar."
        )

    return DraftResult(
        text=text,
        warnings=tuple(risks),
        regenerated=True,
        fallback=True,
    )
