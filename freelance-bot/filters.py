from config import KEYWORDS


def matches(text: str) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in KEYWORDS)
