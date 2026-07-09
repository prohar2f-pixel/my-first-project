"""
Deterministic estimate calculator.

LLM never does arithmetic — all money math lives here.
Uses decimal.Decimal only. verify_estimate() must pass before export.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Literal

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0.00")

ItemType = Literal["material", "work"]
Confidence = Literal["high", "medium", "low", "none"]


def to_decimal(value) -> Decimal | None:
    """Parse qty/price into Decimal. Accepts int/float/str with comma. None if invalid."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
        if not s or s.lower() in {"-", "—", "–", "нет", "n/a", "na"}:
            return None
        try:
            return Decimal(s)
        except (InvalidOperation, ValueError):
            pass
        num: list[str] = []
        for ch in s:
            if ch.isdigit() or ch == ".":
                num.append(ch)
            elif ch in "+-" and not num:
                num.append(ch)
            elif num:
                break
        if not num:
            return None
        try:
            return Decimal("".join(num))
        except (InvalidOperation, ValueError):
            return None
    return None


def money(value: Decimal) -> Decimal:
    """Round to 2 decimal places, HALF_UP."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass
class LineInput:
    type: ItemType
    name: str
    unit: str | None = None
    qty: Decimal | None = None
    unit_price: Decimal | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    confidence: Confidence = "none"
    source: str | None = None
    raw: str | None = None


@dataclass
class LineResult:
    type: ItemType
    name: str
    unit: str | None
    qty: Decimal | None
    unit_price: Decimal | None
    price_min: Decimal | None
    price_max: Decimal | None
    confidence: Confidence
    source: str | None
    line_sum: Decimal | None
    sum_min: Decimal | None
    sum_max: Decimal | None
    included_in_total: bool
    skip_reason: str | None = None


@dataclass
class EstimateResult:
    lines: list[LineResult] = field(default_factory=list)
    total_materials: Decimal = ZERO
    total_works: Decimal = ZERO
    grand_total: Decimal = ZERO
    total_materials_min: Decimal = ZERO
    total_materials_max: Decimal = ZERO
    total_works_min: Decimal = ZERO
    total_works_max: Decimal = ZERO
    grand_total_min: Decimal = ZERO
    grand_total_max: Decimal = ZERO
    skipped_count: int = 0
    materials_count: int = 0
    works_count: int = 0
    included_count: int = 0
    verified: bool = False
    verify_error: str | None = None

    def caption_totals(self) -> str:
        def fmt(d: Decimal) -> str:
            return f"{d:,.2f}".replace(",", " ").replace(".", ",")

        lines = [
            f"Материалы: {fmt(self.total_materials)} ₽ ({self.materials_count} поз.)",
            f"Работы: {fmt(self.total_works)} ₽ ({self.works_count} поз.)",
            f"ИТОГО: {fmt(self.grand_total)} ₽",
        ]
        if self.grand_total_min != self.grand_total or self.grand_total_max != self.grand_total:
            lines.append(
                f"Вилка: {fmt(self.grand_total_min)} – {fmt(self.grand_total_max)} ₽"
            )
        if self.skipped_count:
            lines.append(f"⚠ Вне итога: {self.skipped_count} поз. (нет qty/цены)")
        if self.verified:
            lines.append("✓ Расчёт перепроверен калькулятором")
        return "\n".join(lines)


def _line_product(qty: Decimal | None, price: Decimal | None) -> Decimal | None:
    if qty is None or price is None:
        return None
    if qty < 0 or price < 0:
        return None
    return money(qty * price)


def _calc_line(item: LineInput) -> LineResult:
    qty = item.qty
    price = item.unit_price
    skip_reason = None
    included = False
    line_sum = None

    item_type: ItemType = item.type if item.type in ("material", "work") else "material"

    if item.type not in ("material", "work"):
        skip_reason = "неизвестный тип"
    elif qty is not None and qty < 0:
        skip_reason = "отрицательное количество"
    elif price is not None and price < 0:
        skip_reason = "отрицательная цена"
    elif qty is None and price is None:
        skip_reason = "нет количества и цены"
    elif qty is None:
        skip_reason = "нет количества"
    elif price is None:
        skip_reason = "нет цены"
    else:
        line_sum = _line_product(qty, price)
        if line_sum is None:
            skip_reason = "не удалось посчитать сумму"
        else:
            included = True

    if qty is None:
        sum_min = None
        sum_max = None
    else:
        sum_min = _line_product(qty, item.price_min)
        sum_max = _line_product(qty, item.price_max)

    conf: Confidence = (
        item.confidence if item.confidence in ("high", "medium", "low", "none") else "none"
    )

    return LineResult(
        type=item_type,
        name=item.name or "—",
        unit=item.unit,
        qty=qty,
        unit_price=price,
        price_min=item.price_min,
        price_max=item.price_max,
        confidence=conf,
        source=item.source,
        line_sum=line_sum if included else None,
        sum_min=sum_min,
        sum_max=sum_max,
        included_in_total=included,
        skip_reason=skip_reason,
    )


def calculate_estimate(items: list[LineInput]) -> EstimateResult:
    """Primary calculation pass. verified=False until verify_estimate()."""
    lines = [_calc_line(item) for item in items]

    total_m = ZERO
    total_w = ZERO
    total_m_min = ZERO
    total_m_max = ZERO
    total_w_min = ZERO
    total_w_max = ZERO
    skipped = 0
    materials_count = 0
    works_count = 0
    included = 0

    for line in lines:
        if line.type == "material":
            materials_count += 1
        else:
            works_count += 1

        if line.included_in_total and line.line_sum is not None:
            included += 1
            if line.type == "material":
                total_m = money(total_m + line.line_sum)
                add_min = line.sum_min if line.sum_min is not None else line.line_sum
                add_max = line.sum_max if line.sum_max is not None else line.line_sum
                total_m_min = money(total_m_min + add_min)
                total_m_max = money(total_m_max + add_max)
            else:
                total_w = money(total_w + line.line_sum)
                add_min = line.sum_min if line.sum_min is not None else line.line_sum
                add_max = line.sum_max if line.sum_max is not None else line.line_sum
                total_w_min = money(total_w_min + add_min)
                total_w_max = money(total_w_max + add_max)
        else:
            skipped += 1

    return EstimateResult(
        lines=lines,
        total_materials=total_m,
        total_works=total_w,
        grand_total=money(total_m + total_w),
        total_materials_min=total_m_min,
        total_materials_max=total_m_max,
        total_works_min=total_w_min,
        total_works_max=total_w_max,
        grand_total_min=money(total_m_min + total_w_min),
        grand_total_max=money(total_m_max + total_w_max),
        skipped_count=skipped,
        materials_count=materials_count,
        works_count=works_count,
        included_count=included,
        verified=False,
        verify_error=None,
    )


def verify_estimate(result: EstimateResult) -> EstimateResult:
    """
    Second independent pass. Recalculates every line and totals from scratch.
    Sets verified=True only if all checks match to the kopeck.
    """
    errors: list[str] = []

    recalc_m = ZERO
    recalc_w = ZERO
    recalc_m_min = ZERO
    recalc_m_max = ZERO
    recalc_w_min = ZERO
    recalc_w_max = ZERO
    recalc_skipped = 0
    recalc_included = 0
    recalc_materials = 0
    recalc_works = 0

    for i, line in enumerate(result.lines):
        expected_sum = _line_product(line.qty, line.unit_price)
        should_include = (
            line.qty is not None
            and line.unit_price is not None
            and line.qty >= 0
            and line.unit_price >= 0
            and expected_sum is not None
        )

        if line.type == "material":
            recalc_materials += 1
        else:
            recalc_works += 1

        if should_include:
            if line.line_sum != expected_sum:
                errors.append(
                    f"строка {i + 1} «{line.name}»: line_sum {line.line_sum} != {expected_sum}"
                )
            if not line.included_in_total:
                errors.append(f"строка {i + 1} «{line.name}»: должна быть в итоге")
            recalc_included += 1
            if line.type == "material":
                recalc_m = money(recalc_m + expected_sum)  # type: ignore[arg-type]
            else:
                recalc_w = money(recalc_w + expected_sum)  # type: ignore[arg-type]

            smin = _line_product(line.qty, line.price_min)
            smax = _line_product(line.qty, line.price_max)
            add_min = smin if smin is not None else expected_sum
            add_max = smax if smax is not None else expected_sum
            if line.type == "material":
                recalc_m_min = money(recalc_m_min + add_min)  # type: ignore[arg-type]
                recalc_m_max = money(recalc_m_max + add_max)  # type: ignore[arg-type]
            else:
                recalc_w_min = money(recalc_w_min + add_min)  # type: ignore[arg-type]
                recalc_w_max = money(recalc_w_max + add_max)  # type: ignore[arg-type]
        else:
            recalc_skipped += 1
            if line.included_in_total:
                errors.append(f"строка {i + 1} «{line.name}»: не должна быть в итоге")

        if should_include and expected_sum is not None and line.qty is not None and line.unit_price is not None:
            kopecks = int((line.qty * line.unit_price * 100).to_integral_value(rounding=ROUND_HALF_UP))
            from_line = int((expected_sum * 100).to_integral_value(rounding=ROUND_HALF_UP))
            if kopecks != from_line:
                errors.append(
                    f"строка {i + 1}: integer-kopeck mismatch {kopecks} vs {from_line}"
                )

    recalc_grand = money(recalc_m + recalc_w)
    recalc_grand_min = money(recalc_m_min + recalc_w_min)
    recalc_grand_max = money(recalc_m_max + recalc_w_max)

    if result.total_materials != recalc_m:
        errors.append(f"total_materials {result.total_materials} != {recalc_m}")
    if result.total_works != recalc_w:
        errors.append(f"total_works {result.total_works} != {recalc_w}")
    if result.grand_total != recalc_grand:
        errors.append(f"grand_total {result.grand_total} != {recalc_grand}")
    if result.grand_total != money(result.total_materials + result.total_works):
        errors.append("grand_total != materials + works")
    if result.skipped_count != recalc_skipped:
        errors.append(f"skipped_count {result.skipped_count} != {recalc_skipped}")
    if result.included_count != recalc_included:
        errors.append(f"included_count {result.included_count} != {recalc_included}")
    if result.materials_count != recalc_materials:
        errors.append("materials_count mismatch")
    if result.works_count != recalc_works:
        errors.append("works_count mismatch")
    if result.grand_total_min != recalc_grand_min:
        errors.append(f"grand_total_min {result.grand_total_min} != {recalc_grand_min}")
    if result.grand_total_max != recalc_grand_max:
        errors.append(f"grand_total_max {result.grand_total_max} != {recalc_grand_max}")

    m_k = int((result.total_materials * 100).to_integral_value(rounding=ROUND_HALF_UP))
    w_k = int((result.total_works * 100).to_integral_value(rounding=ROUND_HALF_UP))
    g_k = int((result.grand_total * 100).to_integral_value(rounding=ROUND_HALF_UP))
    if m_k + w_k != g_k:
        errors.append(f"kopeck grand {g_k} != {m_k}+{w_k}")

    if errors:
        result.verified = False
        result.verify_error = "; ".join(errors[:10])
        if len(errors) > 10:
            result.verify_error += f" … +{len(errors) - 10} more"
    else:
        result.verified = True
        result.verify_error = None

    return result


def build_and_verify(items: list[LineInput]) -> EstimateResult:
    """Calculate then verify. Ready for export only if result.verified."""
    return verify_estimate(calculate_estimate(items))
