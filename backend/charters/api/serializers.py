"""Booking serializers. Input parsing and field messages only; rules live in models/services.

Error messages are the exact strings from the prototype's `validateForm`
(docs/UI_GUIDE.md), so the form can show the API's errors as-is.
"""

from decimal import Decimal

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from charters.models import TEXT_LIMIT, Contract, Driver, Terminal, TripUnit, ZipCode
from charters.money import parse_money
from charters.services import contract_limit_reached, create_contract, load_seed, update_contract
from charters.timeutil import format_hhmm, parse_loose_time


def msgs(text: str, *keys: str) -> dict[str, str]:
    """The same message for every listed DRF error key."""
    return dict.fromkeys(keys or ("required", "blank", "null", "invalid"), text)


def state_codes() -> set[str]:
    return {s["code"] for s in load_seed()["states"]}


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------


@extend_schema_field({"type": "string", "example": "07:15", "nullable": True})
class LooseTimeField(serializers.Field):
    """R02 time input: accepts `730`, `7:30`, `7p`... and returns `HH:MM` (R01).

    With `one_way=True`, `null`, `ow` and `one way` mean One way (R03).
    """

    def __init__(self, *, one_way: bool = False, required_msg: str, invalid_msg: str, **kw):
        self.one_way = one_way
        kw.setdefault("allow_null", one_way)
        super().__init__(**kw)
        self.error_messages.update(required=required_msg, null=required_msg, invalid=invalid_msg)

    def to_internal_value(self, data):
        if data is None or (isinstance(data, str) and not data.strip()):
            self.fail("required")
        try:
            return parse_loose_time(str(data), allow_one_way=self.one_way)
        except ValueError:
            self.fail("invalid")

    def to_representation(self, value):
        return format_hhmm(value)


@extend_schema_field(OpenApiTypes.DECIMAL)
class MoneyField(serializers.Field):
    """R13 money input: `1200`, `1,200`, `$1,200.00`. Output is a decimal string."""

    def __init__(self, *, invalid_msg: str, blank_is_zero: bool = True, **kw):
        self.blank_is_zero = blank_is_zero
        super().__init__(**kw)
        self.error_messages.update(required=invalid_msg, null=invalid_msg, invalid=invalid_msg)

    def to_internal_value(self, data):
        if data is None or (isinstance(data, str) and not data.strip()):
            if self.blank_is_zero:
                return Decimal("0.00")
            self.fail("required")
        try:
            amount = parse_money(data)
        except ValueError:
            self.fail("invalid")
        if amount >= Decimal("100000000"):  # DecimalField(10, 2)
            self.fail("invalid")
        return amount

    def to_representation(self, value):
        return f"{value:.2f}"


def location_serializer(prefix: str, label: str) -> type[serializers.Serializer]:
    """Nested `pickup` / `destination` object mapped onto the flat `{prefix}_*` columns."""

    class LocationSerializer(serializers.Serializer):
        location = serializers.CharField(
            source=f"{prefix}_location", max_length=120, required=False, allow_blank=True
        )
        address = serializers.CharField(
            source=f"{prefix}_address", max_length=120, required=False, allow_blank=True
        )
        city = serializers.CharField(
            source=f"{prefix}_city", max_length=60, required=False, allow_blank=True
        )
        state = serializers.CharField(
            source=f"{prefix}_state", max_length=2, required=False, allow_blank=True
        )
        zip = serializers.RegexField(
            r"^\d{5}$",
            source=f"{prefix}_zip",
            required=False,
            allow_blank=True,
            error_messages={"invalid": "Enter a 5-digit ZIP code."},
        )
        county = serializers.CharField(source=f"{prefix}_county", read_only=True)

        def validate(self, attrs):
            """R08 required parts of a location; R09 a known ZIP fills city and state."""
            partial = self.root.partial
            zip_code = attrs.get(f"{prefix}_zip")
            if zip_code:
                hit = ZipCode.objects.filter(zip=zip_code).first()
                if hit:
                    for key, value in (("city", hit.city), ("state", hit.state)):
                        if not attrs.get(f"{prefix}_{key}"):
                            attrs[f"{prefix}_{key}"] = value

            def missing(key: str) -> bool:
                field = f"{prefix}_{key}"
                return (not partial or field in attrs) and not attrs.get(field, "").strip()

            errors = {}
            state = attrs.get(f"{prefix}_state")
            if missing("state") or missing("city") or (state and state not in state_codes()):
                errors["city"] = [f"Pick the {label} state and city."]
            if missing("address"):
                errors["address"] = [f"Enter the {label} address."]
            if errors:
                raise serializers.ValidationError(errors)
            return attrs

    LocationSerializer.__name__ = f"{label.title()}Location"
    return LocationSerializer


PickupSerializer = location_serializer("pickup", "pickup")
DestinationSerializer = location_serializer("dest", "destination")


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


class ContractUnitSerializer(serializers.ModelSerializer):
    """A unit as shown in the contract view's Dispatch section."""

    display_number = serializers.CharField(read_only=True)
    driver = serializers.CharField(source="driver.name", default=None, read_only=True)
    driver_phone = serializers.CharField(source="driver.phone", default=None, read_only=True)
    bus = serializers.CharField(source="bus.number", default=None, read_only=True)

    class Meta:
        model = TripUnit
        fields = [
            "id",
            "display_number",
            "is_duplicate",
            "driver",
            "driver_phone",
            "bus",
            "report_time",
            "actual_report_time",
            "confirm_initials",
            "confirmed_at",
            "dispatch_notes",
        ]


def balance_field():
    return serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class ContractListSerializer(serializers.ModelSerializer):
    balance_due = balance_field()

    class Meta:
        model = Contract
        fields = [
            "id",
            "number",
            "status",
            "begin_date",
            "start_time",
            "organization",
            "group_name",
            "pickup_city",
            "dest_city",
            "bus_count",
            "total_price",
            "balance_due",
            "payment_status",
            "payment_tone",
        ]


class ContractSerializer(serializers.ModelSerializer):
    """Contract detail; also the create / update body."""

    status = serializers.ChoiceField(choices=Contract.Status.choices, required=False)
    organization = serializers.CharField(
        max_length=80, error_messages=msgs("Enter the organization.")
    )
    group_name = serializers.CharField(max_length=80, error_messages=msgs("Enter the group name."))
    passengers = serializers.IntegerField(
        min_value=1,
        max_value=32767,
        error_messages=msgs(
            "Enter the number of passengers.",
            "required",
            "null",
            "invalid",
            "min_value",
            "max_value",
            "max_string_length",
        ),
    )
    contact_name = serializers.CharField(
        max_length=80, error_messages=msgs("Enter the group contact name.")
    )
    contact_phone = serializers.CharField(
        max_length=30, error_messages=msgs("Enter the group contact phone.")
    )
    begin_date = serializers.DateField(error_messages=msgs("Pick a begin date."))
    spot_time = LooseTimeField(
        required_msg="Enter a spot time.",
        invalid_msg="Spot time isn’t a valid time. Try something like 06:45.",
    )
    start_time = LooseTimeField(
        required_msg="Enter a start time.",
        invalid_msg="Start time isn’t a valid time. Try something like 07:15.",
    )
    return_date = serializers.DateField(error_messages=msgs("Pick a return date."))
    return_time = LooseTimeField(
        one_way=True,
        required_msg="Enter a return time, or pick One way.",
        invalid_msg="Return time isn’t a valid time. Try something like 18:30, or pick One way.",
    )
    pickup = PickupSerializer(
        source="*", error_messages=msgs("Enter the pickup address.", "required", "null")
    )
    destination = DestinationSerializer(
        source="*", error_messages=msgs("Enter the destination address.", "required", "null")
    )
    itinerary = serializers.CharField(max_length=TEXT_LIMIT, required=False, allow_blank=True)
    bus_count = serializers.IntegerField(
        min_value=1,
        max_value=32767,  # storage size of the column, not a business limit
        error_messages=msgs(
            "Enter how many buses (at least 1).",
            "required",
            "null",
            "invalid",
            "min_value",
            "max_string_length",
        ),
    )
    terminal = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Terminal.objects.all(),
        error_messages=msgs("Pick a terminal.", "required", "null", "invalid", "does_not_exist"),
    )
    size_requirement = serializers.ChoiceField(
        choices=Contract.Size.choices,
        error_messages=msgs("Pick a size requirement.", "required", "null", "invalid_choice"),
    )
    requested_driver = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), allow_null=True, required=False
    )
    requested_driver_name = serializers.CharField(
        source="requested_driver.name", default=None, read_only=True
    )
    info = serializers.CharField(max_length=TEXT_LIMIT, required=False, allow_blank=True)
    total_price = MoneyField(invalid_msg="Enter the total price.", blank_is_zero=False)
    deposit_required = MoneyField(invalid_msg="Deposit must be a dollar amount.", required=False)
    total_paid = MoneyField(invalid_msg="Total paid must be a dollar amount.", required=False)
    balance_due = balance_field()
    units = ContractUnitSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "number",
            "status",
            "organization",
            "group_name",
            "passengers",
            "contact_name",
            "contact_phone",
            "begin_date",
            "spot_time",
            "start_time",
            "return_date",
            "return_time",
            "pickup",
            "destination",
            "itinerary",
            "bus_count",
            "terminal",
            "size_requirement",
            "requested_driver",
            "requested_driver_name",
            "info",
            "total_price",
            "deposit_required",
            "total_paid",
            "balance_due",
            "payment_status",
            "payment_tone",
            "units",
        ]
        read_only_fields = ["number", "payment_status", "payment_tone"]

    def validate(self, attrs):
        """Cross-field checks on the merged (saved + incoming) values: R04, R05, R13."""
        request = self.context["request"]
        if self.instance is None and contract_limit_reached(request.user):
            raise serializers.ValidationError("Demo limit reached.")

        def value(field):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, None)

        errors = {}
        begin, ret = value("begin_date"), value("return_date")
        if begin and ret and ret < begin:
            errors["return_date"] = ["Return date can’t be before the begin date."]
        spot, start = value("spot_time"), value("start_time")
        if spot and start and spot > start:
            errors["spot_time"] = ["Spot time can’t be after the start time."]
        price = value("total_price")
        deposit = value("deposit_required") or Decimal("0")
        if price is not None and deposit > price:
            errors["deposit_required"] = ["Deposit can’t be more than the total price."]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        owner = validated_data.pop("owner")
        return create_contract(owner, validated_data)

    def update(self, instance, validated_data):
        return update_contract(instance, validated_data)


class PricingQuerySerializer(serializers.Serializer):
    """Unsaved pricing values, for the form's live Balance due / Payment status."""

    status = serializers.ChoiceField(choices=Contract.Status.choices, required=False)
    total_price = serializers.CharField(required=False, allow_blank=True)
    deposit_required = MoneyField(invalid_msg="Deposit must be a dollar amount.", required=False)
    total_paid = MoneyField(invalid_msg="Total paid must be a dollar amount.", required=False)

    def validate_total_price(self, value):
        if not value.strip():
            return None
        try:
            return parse_money(value)
        except ValueError as exc:
            raise serializers.ValidationError("Enter the total price.") from exc
