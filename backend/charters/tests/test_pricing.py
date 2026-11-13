"""Pricing rules R11-R13."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from charters.money import format_money, parse_money

D = Decimal

# --- R11 balance due --------------------------------------------------------


@pytest.mark.django_db
def test_r11_balance_due_is_price_minus_paid(make_contract):
    c = make_contract(total_price=D("2900"), deposit_required=D("600"), total_paid=D("600"))
    assert c.balance_due == D("2300.00")


@pytest.mark.django_db
def test_r11_deposit_alone_never_reduces_balance(make_contract):
    c = make_contract(total_price=D("950"), deposit_required=D("500"), total_paid=D("0"))
    assert c.balance_due == D("950.00")


@pytest.mark.django_db
def test_r11_balance_never_negative_when_overpaid(make_contract):
    c = make_contract(total_price=D("1000"), total_paid=D("1200"))
    assert c.balance_due == D("0.00")


# --- R12 payment status -----------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("price", "deposit", "paid", "status", "tone"),
    [
        ("2450", "500", "2450", "Paid in full", "ok"),
        ("2450", "500", "3000", "Paid in full", "ok"),
        ("2900", "600", "600", "Deposit paid", "part"),
        ("2900", "600", "1000", "Deposit paid", "part"),
        ("2900", "600", "300", "Partially paid", "part"),
        ("2900", "0", "300", "Partially paid", "part"),
        ("950", "0", "0", "Unpaid", "warn"),
        ("950", "500", "0", "Unpaid", "warn"),
        # A free trip with nothing paid is not "Paid in full" (needs total_price > 0).
        ("0", "0", "0", "Unpaid", "warn"),
    ],
)
def test_r12_payment_status(make_contract, price, deposit, paid, status, tone):
    c = make_contract(total_price=D(price), deposit_required=D(deposit), total_paid=D(paid))
    assert c.payment_status == status
    assert c.payment_tone == tone


@pytest.mark.django_db
def test_r12_payment_status_paid_in_full(make_contract):
    c = make_contract(total_price=D("2450"), deposit_required=D("500"), total_paid=D("2450"))
    assert c.payment_status == "Paid in full"


@pytest.mark.django_db
def test_r12_payment_status_deposit_paid(make_contract):
    c = make_contract(total_price=D("2900"), deposit_required=D("600"), total_paid=D("600"))
    assert c.payment_status == "Deposit paid"


@pytest.mark.django_db
def test_r12_payment_status_partially_paid(make_contract):
    c = make_contract(total_price=D("2900"), deposit_required=D("600"), total_paid=D("100"))
    assert c.payment_status == "Partially paid"


@pytest.mark.django_db
def test_r12_payment_status_unpaid(make_contract):
    assert make_contract().payment_status == "Unpaid"


@pytest.mark.django_db
def test_r12_payment_status_cancelled_without_payment(make_contract):
    c = make_contract(status="cancelled", total_price=D("1100"))
    assert c.payment_status == "Cancelled"
    assert c.payment_tone == "none"
    assert c.balance_due == D("0.00")


@pytest.mark.django_db
def test_r12_payment_status_cancelled_keeps_money(make_contract):
    c = make_contract(
        status="cancelled", total_price=D("1100"), deposit_required=D("400"), total_paid=D("400")
    )
    assert c.payment_status == "Cancelled · $400.00 kept"
    assert c.payment_tone == "none"
    assert c.balance_due == D("0.00")


@pytest.mark.django_db
def test_r12_cancelled_wins_over_paid_in_full(make_contract):
    c = make_contract(status="cancelled", total_price=D("500"), total_paid=D("500"))
    assert c.payment_status == "Cancelled · $500.00 kept"


@pytest.mark.django_db
def test_r12_quote_uses_normal_payment_status(make_contract):
    c = make_contract(status="quote", total_price=D("500"), total_paid=D("0"))
    assert c.payment_status == "Unpaid"


# --- R13 money validation ---------------------------------------------------


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("1200", "1200.00"),
        ("1,200", "1200.00"),
        ("$1,200.00", "1200.00"),
        (" $ 1,200.5 ", "1200.50"),
        ("0", "0.00"),
        (1200, "1200.00"),
        (D("99.9"), "99.90"),
    ],
)
def test_r13_parse_money_accepts_loose_input(typed, expected):
    assert parse_money(typed) == D(expected)


@pytest.mark.parametrize("typed", ["", "abc", "-5", "$-5.00", "12.345", "1.2.3", "1,20a"])
def test_r13_parse_money_rejects_bad_input(typed):
    with pytest.raises(ValueError, match="Enter a valid amount"):
        parse_money(typed)


def test_r13_parse_money_rejects_negative_decimal():
    with pytest.raises(ValueError):
        parse_money(D("-1"))


@pytest.mark.parametrize(
    ("amount", "shown"),
    [(D("1200"), "$1,200.00"), (D("0"), "$0.00"), (D("1234567.5"), "$1,234,567.50"), (5, "$5.00")],
)
def test_r13_format_money(amount, shown):
    assert format_money(amount) == shown


@pytest.mark.django_db
def test_r13_deposit_above_price_fails_validation(make_contract):
    c = make_contract()
    c.deposit_required = D("1000")  # price is 950
    with pytest.raises(ValidationError) as exc:
        c.full_clean()
    assert "deposit_required" in exc.value.message_dict


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["total_price", "deposit_required", "total_paid"])
def test_r13_negative_amount_fails_validation(make_contract, field):
    c = make_contract()
    setattr(c, field, D("-1"))
    with pytest.raises(ValidationError) as exc:
        c.full_clean()
    assert field in exc.value.message_dict


@pytest.mark.django_db
def test_r13_database_rejects_deposit_above_price(make_contract):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_contract(total_price=D("100"), deposit_required=D("200"))


@pytest.mark.django_db
def test_r13_database_rejects_negative_paid(make_contract):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_contract(total_paid=D("-1"))


@pytest.mark.django_db
def test_r13_deposit_equal_to_price_is_allowed(make_contract):
    c = make_contract(total_price=D("950"), deposit_required=D("950"))
    c.full_clean()
