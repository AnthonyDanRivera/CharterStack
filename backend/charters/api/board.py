"""Dispatch endpoints: /api/board/, /api/board/export.xlsx and /api/units/ (docs/API.md)."""

import datetime as dt
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from charters import board
from charters.models import TEXT_LIMIT, Bus, Driver, Terminal, TripUnit
from charters.timeutil import today_in

from .ownership import OwnedGenericViewSet, owned
from .serializers import LooseTimeField

# ---------------------------------------------------------------------------
# Query parameters
# ---------------------------------------------------------------------------


class BoardParams(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    view = serializers.ChoiceField(choices=board.VIEWS, default="today")
    terminals = serializers.CharField(required=False, allow_blank=True)
    q = serializers.CharField(required=False, allow_blank=True, default="")
    sort = serializers.ChoiceField(choices=board.COLUMNS, required=False)
    dir = serializers.ChoiceField(choices=["asc", "desc"], default="asc")


class ExportParams(BoardParams):
    columns = serializers.CharField(required=False, allow_blank=True)
    widths = serializers.CharField(required=False, allow_blank=True)


def board_query(request: Request, params_class=BoardParams) -> tuple[board.BoardQuery, dict]:
    """R24: the range defaults to today/today in the visitor's time zone."""
    params = params_class(data=request.query_params)
    params.is_valid(raise_exception=True)
    data = params.validated_data
    today = today_in_request()
    start = data.get("start") or data.get("end") or today
    end = data.get("end") or data.get("start") or today
    if end < start:
        raise ValidationError({"end": ["End date can't be before the start date."]})
    terminals = None
    if "terminals" in data:
        terminals = [t.strip().upper() for t in data["terminals"].split(",") if t.strip()]
    query = board.BoardQuery(
        start=start,
        end=end,
        view=data["view"],
        terminals=terminals,
        q=data["q"],
        sort=data.get("sort"),
        direction=data["dir"],
    )
    return query, data


def today_in_request() -> dt.date:
    """Today in the visitor's zone (activated by VisitorTimezoneMiddleware)."""
    return today_in(timezone.get_current_timezone())


BOARD_PARAMETERS = [
    OpenApiParameter("start", OpenApiTypes.DATE, description="Range start (default today)"),
    OpenApiParameter("end", OpenApiTypes.DATE, description="Range end (default today)"),
    OpenApiParameter("view", str, enum=list(board.VIEWS), description="R25 trip view"),
    OpenApiParameter(
        "terminals", str, description="Comma-separated codes; omitted = all; empty = none"
    ),
    OpenApiParameter("q", str, description="Search text (rows only, not counts)"),
    OpenApiParameter("sort", str, enum=board.COLUMNS, description="Column key"),
    OpenApiParameter("dir", str, enum=["asc", "desc"]),
]


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------


class BoardRowSerializer(serializers.Serializer):
    """Documents the row shape for Swagger; rows are built in charters/board.py."""

    id = serializers.IntegerField()
    contract_id = serializers.IntegerField()
    contract_number = serializers.IntegerField()
    display_number = serializers.CharField()
    is_duplicate = serializers.BooleanField()
    day_label = serializers.CharField()
    is_multi_day = serializers.BooleanField()
    terminal = serializers.CharField()
    begin_date = serializers.DateField()
    start_time = serializers.CharField()
    spot_time = serializers.CharField()
    report_time = serializers.CharField(allow_null=True)
    actual_report_time = serializers.CharField(allow_null=True)
    actual_report_late = serializers.BooleanField()
    on_location_time = serializers.CharField(allow_null=True)
    organization = serializers.CharField()
    group_name = serializers.CharField()
    pickup = serializers.CharField()
    destination = serializers.CharField()
    return_date = serializers.DateField()
    return_time = serializers.CharField(allow_null=True)
    driver = serializers.CharField(allow_null=True)
    driver_phone = serializers.CharField(allow_null=True)
    bus = serializers.CharField(allow_null=True)
    bus_seats = serializers.IntegerField(allow_null=True)
    size_requirement = serializers.CharField()
    needs_wc = serializers.BooleanField()
    confirm_initials = serializers.CharField()
    confirmed_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    dispatch_notes = serializers.CharField()


class BoardResponseSerializer(serializers.Serializer):
    counts = serializers.DictField(child=serializers.IntegerField())
    refreshed_at = serializers.DateTimeField()
    rows = BoardRowSerializer(many=True)


@extend_schema(
    summary="Dispatch board",
    description="Rows for the range, view, terminals and search; counts ignore the search (R29).",
    parameters=BOARD_PARAMETERS,
    responses=BoardResponseSerializer,
)
@api_view(["GET"])
def board_view(request: Request) -> Response:
    query, _ = board_query(request)
    return Response(board.build_board(owned(TripUnit, request.user), query))


@extend_schema(
    summary="Export the board to Excel",
    parameters=[
        *BOARD_PARAMETERS,
        OpenApiParameter("columns", str, description="Column keys in display order"),
        OpenApiParameter("widths", str, description="Column widths in px, same order"),
    ],
    responses={(200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): bytes},
)
@api_view(["GET"])
def board_export(request: Request) -> HttpResponse:
    query, data = board_query(request, ExportParams)
    columns = [c.strip() for c in (data.get("columns") or "").split(",") if c.strip()]
    columns = columns or list(board.COLUMNS)
    unknown = [c for c in columns if c not in board.COLUMNS]
    if unknown:
        raise ValidationError({"columns": [f"Unknown column: {', '.join(unknown)}"]})
    widths = None
    if data.get("widths"):
        try:
            widths = [int(w) for w in data["widths"].split(",")]
        except ValueError as exc:
            raise ValidationError({"widths": ["Widths must be whole numbers."]}) from exc

    rows = board.build_board(owned(TripUnit, request.user), query)["rows"]
    workbook = board.export_workbook(rows, columns, widths)
    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="CharterStack-board-{query.start.isoformat()}.xlsx"'
    )
    return response


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


class UnitPatchSerializer(serializers.Serializer):
    """Dispatch fields a unit PATCH may change (R17, R22, R23)."""

    driver = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), allow_null=True, required=False
    )
    bus = serializers.PrimaryKeyRelatedField(
        queryset=Bus.objects.all(), allow_null=True, required=False
    )
    report_time = LooseTimeField(
        required=False,
        allow_null=True,
        required_msg="Enter a valid time",
        invalid_msg="Enter a valid time",
    )
    confirm_initials = serializers.CharField(required=False, allow_blank=True, max_length=40)
    dispatch_notes = serializers.CharField(
        required=False, allow_blank=True, max_length=TEXT_LIMIT, trim_whitespace=False
    )

    def to_internal_value(self, data):
        # A blank report time means "not set" (R17), not an error.
        if isinstance(data, dict) and data.get("report_time") == "":
            data = {**data, "report_time": None}
        return super().to_internal_value(data)


def unit_detail(unit: TripUnit, start: dt.date, end: dt.date) -> dict:
    """The board row plus what the Trip information and Assign panels need."""
    c = unit.contract
    row = board.public(board.board_row(unit, start, end))
    row.update(
        {
            "passengers": c.passengers,
            "contact_name": c.contact_name,
            "contact_phone": c.contact_phone,
            "info": c.info,
            "itinerary": c.itinerary,
            "requested_driver": c.requested_driver_id,
            "requested_driver_name": c.requested_driver.name if c.requested_driver else None,
            "bus_count": c.bus_count,
            "driver_id": unit.driver_id,
            "bus_id": unit.bus_id,
        }
    )
    return row


class UnitDetailSerializer(BoardRowSerializer):
    passengers = serializers.IntegerField()
    contact_name = serializers.CharField()
    contact_phone = serializers.CharField()
    info = serializers.CharField()
    itinerary = serializers.CharField()
    requested_driver = serializers.IntegerField(allow_null=True)
    requested_driver_name = serializers.CharField(allow_null=True)
    bus_count = serializers.IntegerField()
    driver_id = serializers.IntegerField(allow_null=True)
    bus_id = serializers.IntegerField(allow_null=True)


class UnitWithWarningsSerializer(UnitDetailSerializer):
    warnings = serializers.ListField(child=serializers.CharField())


class UnitViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    OwnedGenericViewSet,
):
    model = TripUnit
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    serializer_class = UnitDetailSerializer

    def get_queryset(self):
        return board.board_units(super().get_queryset())

    def detail_response(self, unit: TripUnit, code: int = 200, **extra) -> Response:
        today = today_in_request()
        unit = self.get_queryset().get(pk=unit.pk)  # fresh, with related rows
        return Response({**unit_detail(unit, today, today), **extra}, status=code)

    @extend_schema(summary="Unit detail")
    def retrieve(self, request, *args, **kwargs):
        return self.detail_response(self.get_object())

    @extend_schema(
        summary="Assign driver, bus, report time; edit initials and notes",
        request=UnitPatchSerializer,
        responses=UnitWithWarningsSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        unit = self.get_object()
        patch = UnitPatchSerializer(data=request.data)
        patch.is_valid(raise_exception=True)
        data = patch.validated_data
        for field in ("driver", "bus", "report_time", "dispatch_notes"):
            if field in data:
                setattr(unit, field, data[field])
        if "confirm_initials" in data:
            board.set_initials(unit, data["confirm_initials"])
        unit.save()
        unit = self.get_queryset().get(pk=unit.pk)
        return self.detail_response(unit, warnings=board.bus_warnings(unit.contract, unit.bus))

    def update(self, request, *args, **kwargs):
        if not kwargs.get("partial"):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a duplicate",
        responses={204: None, 400: OpenApiResponse(description="Not a duplicate")},
    )
    def destroy(self, request, *args, **kwargs):
        """R16: only duplicates can be deleted from the board."""
        unit = self.get_object()
        if not unit.is_duplicate:
            raise ValidationError({"detail": "Only duplicates can be deleted."})
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Warnings for a bus choice before saving",
        parameters=[OpenApiParameter("bus", int, description="Bus id")],
        responses=inline_serializer(
            "BusWarnings", {"warnings": serializers.ListField(child=serializers.CharField())}
        ),
    )
    @action(detail=True, methods=["get"])
    def check(self, request, pk=None):
        """R18: capacity and lift warnings for a bus, without saving."""
        unit = self.get_object()
        bus_id = request.query_params.get("bus", "")
        bus = Bus.objects.filter(pk=bus_id).first() if bus_id.isdigit() else None
        return Response({"warnings": board.bus_warnings(unit.contract, bus)})

    @extend_schema(summary="Toggle the Reported stamp (R19)", request=None)
    @action(detail=True, methods=["post"])
    def reported(self, request, pk=None):
        clear = bool(request.data.get("clear")) if hasattr(request.data, "get") else False
        return self.detail_response(board.toggle_reported(self.get_object(), clear=clear))

    @extend_schema(summary="Toggle On location (R20)", request=None)
    @action(detail=True, methods=["post"], url_path="on-location")
    def on_location(self, request, pk=None):
        return self.detail_response(board.toggle_on_location(self.get_object()))

    @extend_schema(summary="Toggle Cancelled on this unit (R21)", request=None)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self.detail_response(board.toggle_cancelled(self.get_object()))

    @extend_schema(summary="Add a duplicate unit (R16)", request=None)
    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        try:
            dup = board.duplicate_unit(self.get_object(), request.user)
        except board.DuplicateLimitReached as exc:
            raise ValidationError({"detail": "Demo limit reached."}) from exc
        return self.detail_response(dup, code=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Bus board
# ---------------------------------------------------------------------------


class BusBoardParams(serializers.Serializer):
    terminal = serializers.CharField(required=False, default="NJ")
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)


class BusBoardResponseSerializer(serializers.Serializer):
    terminal = serializers.DictField(child=serializers.CharField())
    start = serializers.DateField()
    end = serializers.DateField()
    counts = serializers.DictField(child=serializers.IntegerField())
    rows = serializers.ListField(child=serializers.DictField())


@extend_schema(
    summary="Bus board",
    description="R34/R35: a terminal's buses, one row per model in bus-number order, "
    "with their trips in the date range.",
    parameters=[
        OpenApiParameter("terminal", str, description="Terminal code (default NJ)"),
        OpenApiParameter("start", OpenApiTypes.DATE, description="Range start (default today)"),
        OpenApiParameter("end", OpenApiTypes.DATE, description="Range end (default today)"),
    ],
    responses=BusBoardResponseSerializer,
)
@api_view(["GET"])
def bus_board_view(request: Request) -> Response:
    params = BusBoardParams(data=request.query_params)
    params.is_valid(raise_exception=True)
    data = params.validated_data
    today = today_in_request()
    start = data.get("start") or data.get("end") or today
    end = data.get("end") or data.get("start") or today
    if end < start:
        raise ValidationError({"end": ["End date can't be before the start date."]})
    terminal = Terminal.objects.filter(code=data["terminal"].strip().upper()).first()
    if terminal is None:
        raise ValidationError({"terminal": ["Unknown terminal."]})
    return Response(board.bus_board(owned(TripUnit, request.user), terminal, start, end))
