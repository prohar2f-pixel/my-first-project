from database import get_keywords


def matches(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in get_keywords())
