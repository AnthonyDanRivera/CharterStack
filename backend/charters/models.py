"""CharterStack models. See docs/DATA_MODEL.md.

Reference data (Terminal, Driver, Bus, ZipCode) is global. Contract and TripUnit
are visitor-owned: every row has an `owner`, and every query must filter by it
(docs/DEMO_SANDBOX.md).
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .money import format_money

TEXT_LIMIT = 2000  # itinerary, info, dispatch notes (DEMO_SANDBOX.md safeguards)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


class Terminal(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=40)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Driver(models.Model):
    name = models.CharField(max_length=80, unique=True)
    phone = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Bus(models.Model):
    number = models.CharField(max_length=10, unique=True)
    seats = models.PositiveSmallIntegerField()
    model = models.CharField(max_length=40)
    has_wc_lift = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["number"]
        verbose_name_plural = "buses"

    def __str__(self) -> str:
        return f"#{self.number}"


class ZipCode(models.Model):
    """ZIP lookup used to auto-fill city, state and county (R09)."""

    zip = models.CharField(max_length=5, unique=True)
    city = models.CharField(max_length=60)
    state = models.CharField(max_length=2)
    county = models.CharField(max_length=60)

    class Meta:
        ordering = ["zip"]
        verbose_name = "ZIP code"

    def __str__(self) -> str:
        return self.zip


# ---------------------------------------------------------------------------
# Visitor-owned data
# ---------------------------------------------------------------------------


class Contract(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        QUOTE = "quote", "Quote"
        CANCELLED = "cancelled", "Cancelled"

    class Size(models.TextChoices):
        COACH_56 = "56-pax coach"
        COACH_56_WC = "56-pax coach WC"
        COACH_57 = "57-pax coach"
        COACH_57_WC = "57-pax coach WC"
        MINI_35 = "35-pax minicoach"
        MINI_35_WC = "35-pax minicoach WC"
        SHUTTLE_28 = "28-pax shuttle"
        SHUTTLE_28_WC = "28-pax shuttle WC"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contracts"
    )
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.BOOKED)

    organization = models.CharField(max_length=80)
    group_name = models.CharField(max_length=80)
    passengers = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    contact_name = models.CharField(max_length=80)
    contact_phone = models.CharField(max_length=30)

    begin_date = models.DateField()
    spot_time = models.TimeField()
    start_time = models.TimeField()
    return_date = models.DateField()
    return_time = models.TimeField(null=True, blank=True)  # null = One way (R03)

    pickup_location = models.CharField(max_length=120, blank=True)
    pickup_address = models.CharField(max_length=120)
    pickup_city = models.CharField(max_length=60)
    pickup_state = models.CharField(max_length=2)
    pickup_zip = models.CharField(max_length=5, blank=True)
    pickup_county = models.CharField(max_length=60, blank=True)

    dest_location = models.CharField(max_length=120, blank=True)
    dest_address = models.CharField(max_length=120)
    dest_city = models.CharField(max_length=60)
    dest_state = models.CharField(max_length=2)
    dest_zip = models.CharField(max_length=5, blank=True)
    dest_county = models.CharField(max_length=60, blank=True)

    itinerary = models.TextField(max_length=TEXT_LIMIT, blank=True)
    bus_count = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    terminal = models.ForeignKey(Terminal, on_delete=models.PROTECT, related_name="contracts")
    size_requirement = models.CharField(max_length=24, choices=Size.choices)
    requested_driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="requested_on"
    )
    info = models.TextField(max_length=TEXT_LIMIT, blank=True)

    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    deposit_required = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    total_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        indexes = [models.Index(fields=["owner", "begin_date"])]
        constraints = [
            # Also serves as the (owner, number) index.
            models.UniqueConstraint(fields=["owner", "number"], name="contract_number_per_owner"),
            models.CheckConstraint(condition=Q(passengers__gte=1), name="contract_passengers_min"),
            models.CheckConstraint(
                condition=Q(bus_count__gte=1),
                name="contract_bus_count_min",
            ),
            # R13: amounts are 0 or more and the deposit never exceeds the price.
            models.CheckConstraint(
                condition=Q(total_price__gte=0, deposit_required__gte=0, total_paid__gte=0),
                name="contract_money_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(deposit_required__lte=F("total_price")),
                name="contract_deposit_within_price",
            ),
        ]

    def __str__(self) -> str:
        return str(self.number)

    def clean(self) -> None:
        """R13: the deposit can't exceed the total price."""
        super().clean()
        if (
            self.total_price is not None
            and self.deposit_required is not None
            and self.deposit_required > self.total_price
        ):
            raise ValidationError(
                {"deposit_required": "Deposit can't be more than the total price."}
            )

    @property
    def is_cancelled(self) -> bool:
        return self.status == self.Status.CANCELLED

    @property
    def balance_due(self) -> Decimal:
        """R11: `max(0, total_price - total_paid)`. The deposit never reduces it.

        R12: a cancelled contract shows a $0.00 balance.
        """
        if self.is_cancelled:
            return Decimal("0.00")
        return max(Decimal("0.00"), self.total_price - self.total_paid)

    @property
    def payment_status(self) -> str:
        """R12: payment status text, first match wins."""
        if self.is_cancelled:
            if self.total_paid > 0:
                return f"Cancelled · {format_money(self.total_paid)} kept"
            return "Cancelled"
        if self.total_price > 0 and self.total_paid >= self.total_price:
            return "Paid in full"
        if self.deposit_required > 0 and self.total_paid >= self.deposit_required:
            return "Deposit paid"
        if self.total_paid > 0:
            return "Partially paid"
        return "Unpaid"

    @property
    def payment_tone(self) -> str:
        """R12: text color for the payment status: `ok`, `part`, `warn` or `none`."""
        status = self.payment_status
        if status.startswith("Cancelled"):
            return "none"
        return {
            "Paid in full": "ok",
            "Deposit paid": "part",
            "Partially paid": "part",
        }.get(status, "warn")

    @property
    def needs_wc(self) -> bool:
        """A size requirement ending in `WC` needs a wheelchair lift (R18)."""
        return self.size_requirement.endswith("WC")

    @property
    def is_multi_day(self) -> bool:
        return self.return_date > self.begin_date


class TripUnit(models.Model):
    """One bus on one contract: one row on the dispatch board."""

    class Status(models.TextChoices):
        NORMAL = "", "Normal"
        ON_LOCATION = "onloc", "On location"
        CANCELLED = "cancelled", "Cancelled"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trip_units"
    )
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="units")
    unit_number = models.PositiveSmallIntegerField()
    is_duplicate = models.BooleanField(default=False)

    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="units"
    )
    bus = models.ForeignKey(
        Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name="units"
    )
    report_time = models.TimeField(null=True, blank=True)
    actual_report_time = models.TimeField(null=True, blank=True)
    on_location_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, blank=True, default="")
    confirm_initials = models.CharField(max_length=4, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    dispatch_notes = models.TextField(max_length=TEXT_LIMIT, blank=True)

    class Meta:
        # R30 default order: contract, regular units by number, then duplicates.
        ordering = ["contract__number", "is_duplicate", "unit_number"]
        indexes = [models.Index(fields=["owner", "contract"])]
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "is_duplicate", "unit_number"], name="unit_number_per_contract"
            ),
        ]

    def __str__(self) -> str:
        return self.display_number

    def save(self, *args, **kwargs) -> None:
        # A unit always belongs to its contract's owner.
        if self.contract_id and not self.owner_id:
            self.owner_id = self.contract.owner_id
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.contract_id and self.owner_id and self.contract.owner_id != self.owner_id:
            raise ValidationError("A unit must have the same owner as its contract.")

    @property
    def display_number(self) -> str:
        """R15: `24817` single-bus, `24823-1` multi-bus, `24817-D1` duplicate."""
        number = self.contract.number
        if self.is_duplicate:
            return f"{number}-D{self.unit_number}"
        if self.contract.bus_count > 1:
            return f"{number}-{self.unit_number}"
        return str(number)


# ---------------------------------------------------------------------------
# Demo sandbox
# ---------------------------------------------------------------------------


class DemoSession(models.Model):
    """One visitor's sandbox: a throwaway user plus when it started (DEMO_SANDBOX.md)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demo_session"
    )
    short_id = models.CharField(max_length=10, unique=True)  # DEMO-8F3K2
    # A default rather than auto_now_add so tests can create expired sessions.
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.short_id
