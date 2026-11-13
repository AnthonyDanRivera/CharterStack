"""Money parsing and display (rule R13).

Amounts are stored as `Decimal` with two places. Users may type `1200`, `1,200`
or `$1,200.00`; display is always `$1,200.00`.
"""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTS = Decimal("0.01")
_MONEY_RE = re.compile(r"^\d+(\.\d{1,2})?$")


def parse_money(value: str | int | float | Decimal) -> Decimal:
    """Parse a loosely typed amount into a non-negative Decimal (R13).

    Strips `$`, thousands commas and spaces. Raises `ValueError` for anything
    that is not a plain non-negative amount with at most two decimals.
    """
    if isinstance(value, Decimal | int):
        amount = Decimal(value)
    else:
        text = re.sub(r"[$,\s]", "", str(value))
        if not _MONEY_RE.match(text):
            raise ValueError("Enter a valid amount")
        try:
            amount = Decimal(text)
        except InvalidOperation as exc:  # pragma: no cover - regex already guards this
            raise ValueError("Enter a valid amount") from exc
    if amount < 0:
        raise ValueError("Enter a valid amount")
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def format_money(amount: Decimal | int) -> str:
    """Format an amount as `$1,200.00` (R13)."""
    return f"${Decimal(amount).quantize(CENTS, rounding=ROUND_HALF_UP):,.2f}"
