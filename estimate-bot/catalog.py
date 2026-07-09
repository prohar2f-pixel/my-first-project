"""Catalog of common construction works and materials for LLM prompts."""

# Categories and keywords for work type detection
WORK_CATEGORIES = {
    "painting": ["покраска", "окраска", "краски работы", "малярные работы"],
    "flooring": ["укладка пола", "полы", "ламинат", "плитка", "паркет"],
    "walls": ["штукатурка", "обшивка стен", "облицовка", "плитка стен"],
    "electrical": ["электромонтаж", "проводка", "кабель", "розетки"],
    "plumbing": ["водопровод", "канализация", "сантехника", "трубы"],
    "carpentry": ["столярные работы", "двери", "окна", "рамы"],
    "concrete": ["бетонные работы", "стяжка", "фундамент"],
    "roof": ["кровля", "кровельные работы", "крыша"],
    "insulation": ["утепление", "изоляция", "звукоизоляция"],
    "hvac": ["вентиляция", "кондиционирование", "система охлаждения"],
}

MATERIAL_CATEGORIES = {
    "paint": ["краска", "лак", "грунтовка", "эмаль"],
    "flooring": ["ламинат", "плитка пола", "паркет", "ковролин", "линолеум"],
    "wall": ["обои", "плитка", "гипсокартон", "кирпич", "блоки"],
    "wood": ["доски", "брус", "фанера", "ДСП", "ДВП"],
    "metal": ["профиль", "уголок", "труба", "арматура", "железо"],
    "cable": ["кабель", "провод", "электропровод"],
    "insulation": ["минвата", "пенопласт", "изоляция", "утеплитель"],
    "adhesive": ["клей", "герметик", "шпатлевка"],
    "fasteners": ["гвозди", "саморезы", "болты", "шурупы"],
}

# Common units by category
UNITS_BY_CATEGORY = {
    "painting": ["м²", "кв.м", "м2"],
    "flooring": ["м²", "кв.м", "м2"],
    "walls": ["м²", "кв.м", "м2"],
    "electrical": ["м", "погонный метр", "шт", "штук"],
    "plumbing": ["м", "погонный метр", "шт", "штук"],
    "carpentry": ["шт", "штук", "комплект"],
    "concrete": ["м³", "куб.м", "куб"],
    "roof": ["м²", "кв.м", "м2"],
    "paint": ["л", "литр", "кг", "килограмм"],
    "flooring": ["м²", "кв.м", "м2", "м", "погонный метр"],
}

# System prompt extension for work/material classification
CLASSIFICATION_PROMPT = """
Классификация:
- "материал" — физический товар (краска, кирпич, кабель, доски)
- "работа" — услуга (покраска, монтаж, доставка, штукатурка)

Если сомневаешься: "краска" → материал, "покраска" → работа.
"""

def get_category_keywords(category_type: str) -> list[str]:
    """Get keywords for a category (work or material)."""
    if category_type == "work":
        return [kw for keywords in WORK_CATEGORIES.values() for kw in keywords]
    elif category_type == "material":
        return [kw for keywords in MATERIAL_CATEGORIES.values() for kw in keywords]
    return []


def guess_type(name: str) -> str:
    """Guess if name is material or work based on keywords."""
    name_lower = name.lower()
    work_keywords = get_category_keywords("work")
    material_keywords = get_category_keywords("material")

    # Count keyword matches
    work_score = sum(1 for kw in work_keywords if kw in name_lower)
    material_score = sum(1 for kw in material_keywords if kw in name_lower)

    if work_score > material_score:
        return "work"
    elif material_score > work_score:
        return "material"
    else:
        # Default: if it ends with certain suffixes, likely work
        if name_lower.endswith(("работы", "монтаж", "услуга", "услуги")):
            return "work"
        return "material"
