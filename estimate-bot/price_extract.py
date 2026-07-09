"""Utilities for price parsing and normalization."""

from decimal import Decimal
from calculator import to_decimal


def normalize_price(price_value) -> Decimal | None:
    """
    Convert any price value to Decimal.
    Rejects 0 prices (likely missing data), negative prices.
    """
    d = to_decimal(price_value)
    if d is None or d <= 0:
        return None
    return d


def choose_price(price_typical: Decimal | None, price_min: Decimal | None, price_max: Decimal | None) -> Decimal | None:
    """
    Pick the best estimate from typical/min/max.
    Prefer: typical > average(min, max) > min > max.
    """
    if price_typical is not None:
        return price_typical
    if price_min is not None and price_max is not None:
        return (price_min + price_max) / 2
    if price_min is not None:
        return price_min
    if price_max is not None:
        return price_max
    return None
