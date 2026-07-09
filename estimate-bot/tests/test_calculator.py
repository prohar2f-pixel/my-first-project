import pytest
from decimal import Decimal

from calculator import (
    LineInput,
    to_decimal,
    money,
    calculate_estimate,
    verify_estimate,
    build_and_verify,
    ZERO,
)


class TestToDecimal:
    def test_to_decimal_int(self):
        assert to_decimal(10) == Decimal("10")

    def test_to_decimal_str_with_comma(self):
        assert to_decimal("10,5") == Decimal("10.5")

    def test_to_decimal_none(self):
        assert to_decimal(None) is None


class TestMoney:
    def test_money_basic(self):
        assert money(Decimal("10")) == Decimal("10.00")

    def test_money_round_half_up(self):
        assert money(Decimal("1.005")) == Decimal("1.01")


class TestCalculateEstimate:
    def test_empty_list(self):
        result = calculate_estimate([])
        assert result.grand_total == ZERO
        assert result.verified is False

    def test_single_material(self):
        items = [
            LineInput(
                type="material",
                name="Краска",
                qty=Decimal("10"),
                unit_price=Decimal("150"),
            )
        ]
        result = calculate_estimate(items)
        assert result.lines[0].line_sum == Decimal("1500.00")
        assert result.total_materials == Decimal("1500.00")

    def test_materials_and_works(self):
        items = [
            LineInput(
                type="material",
                name="Краска",
                qty=Decimal("10"),
                unit_price=Decimal("150"),
            ),
            LineInput(
                type="work",
                name="Покраска",
                qty=Decimal("80"),
                unit_price=Decimal("300"),
            ),
        ]
        result = calculate_estimate(items)
        assert result.total_materials == Decimal("1500.00")
        assert result.total_works == Decimal("24000.00")
        assert result.grand_total == Decimal("25500.00")

    def test_qty_is_none(self):
        items = [
            LineInput(
                type="material",
                name="Краска",
                qty=None,
                unit_price=Decimal("150"),
            )
        ]
        result = calculate_estimate(items)
        assert result.lines[0].included_in_total is False
        assert result.skipped_count == 1


class TestVerifyEstimate:
    def test_verify_ok(self):
        items = [
            LineInput(
                type="material",
                name="Краска",
                qty=Decimal("10"),
                unit_price=Decimal("150"),
            )
        ]
        result = calculate_estimate(items)
        verified = verify_estimate(result)
        assert verified.verified is True

    def test_verify_fail_corrupted(self):
        items = [
            LineInput(
                type="material",
                name="Краска",
                qty=Decimal("10"),
                unit_price=Decimal("150"),
            )
        ]
        result = calculate_estimate(items)
        result.lines[0].line_sum = Decimal("9999.00")
        result.lines[0].included_in_total = True
        verified = verify_estimate(result)
        assert verified.verified is False


class TestBuildAndVerify:
    def test_build_and_verify_ok(self):
        items = [
            LineInput(
                type="material",
                name="Краска",
                qty=Decimal("10"),
                unit_price=Decimal("150"),
            ),
            LineInput(
                type="work",
                name="Покраска",
                qty=Decimal("80"),
                unit_price=Decimal("300"),
            ),
        ]
        result = build_and_verify(items)
        assert result.verified is True
        assert result.grand_total == Decimal("25500.00")
