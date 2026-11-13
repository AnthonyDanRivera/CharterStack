"""Booking endpoints: /api/contracts/ (docs/API.md)."""

from django.db.models import Prefetch
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from charters.models import Contract, TripUnit
from charters.services import (
    contract_summary,
    filter_contracts,
    lookup_contract,
    next_contract_number,
)

from .ownership import OwnedModelViewSet
from .serializers import ContractListSerializer, ContractSerializer, PricingQuerySerializer

STATUS_FILTERS = ["all", "active", "booked", "quote", "cancelled"]


class ContractListQuery(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    status = serializers.ChoiceField(choices=STATUS_FILTERS, default="all")
    q = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        # One end of the range alone means a single day.
        start, end = attrs.get("start"), attrs.get("end")
        attrs["start"], attrs["end"] = start or end, end or start
        if attrs["start"] and attrs["end"] < attrs["start"]:
            raise serializers.ValidationError({"end": ["End date can't be before the start date."]})
        return attrs


ContractListResponse = inline_serializer(
    "ContractListPage",
    {
        "results": ContractListSerializer(many=True),
        "summary": inline_serializer(
            "ContractSummary",
            {
                "count": serializers.IntegerField(),
                "booked": serializers.IntegerField(),
                "quotes": serializers.IntegerField(),
                "cancelled": serializers.IntegerField(),
                "balance_due": serializers.DecimalField(max_digits=12, decimal_places=2),
            },
        ),
    },
)

PricingResponse = inline_serializer(
    "Pricing",
    {
        "balance_due": serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True),
        "payment_status": serializers.CharField(),
        "payment_tone": serializers.CharField(),
    },
)


@extend_schema_view(
    list=extend_schema(
        summary="List contracts",
        parameters=[ContractListQuery],
        responses=ContractListResponse,
    ),
    retrieve=extend_schema(summary="Contract detail"),
    create=extend_schema(summary="Insert a contract (number assigned by the server)"),
    partial_update=extend_schema(summary="Edit a contract"),
    destroy=extend_schema(summary="Delete a contract and its units"),
)
class ContractViewSet(OwnedModelViewSet):
    model = Contract
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("terminal", "requested_driver")
            .prefetch_related(
                Prefetch(
                    "units",
                    queryset=TripUnit.objects.select_related("driver", "bus").order_by(
                        "is_duplicate", "unit_number"
                    ),
                )
            )
        )

    def get_serializer_class(self):
        return ContractListSerializer if self.action == "list" else ContractSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        """R24 range, R32 status filter, R28 search; R33 summary over the listed rows."""
        query = ContractListQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        contracts = list(
            filter_contracts(self.get_queryset(), **query.validated_data).order_by(
                "begin_date", "number"
            )
        )
        summary = contract_summary(contracts)
        summary["balance_due"] = f"{summary['balance_due']:.2f}"
        return Response(
            {
                "results": ContractListSerializer(contracts, many=True).data,
                "summary": summary,
            }
        )

    @extend_schema(
        summary="Next contract number",
        responses=inline_serializer("NextNumber", {"number": serializers.IntegerField()}),
    )
    @action(detail=False, methods=["get"], url_path="next-number")
    def next_number(self, request: Request) -> Response:
        """R06: shown read-only in the insert form."""
        return Response({"number": next_contract_number(request.user)})

    @extend_schema(
        summary="Look up a contract by number",
        parameters=[OpenApiParameter("number", str, description="`24817`, `24823-2`, `24817-D1`")],
        responses={
            200: inline_serializer("LookupHit", {"id": serializers.IntegerField()}),
            404: OpenApiResponse(description="No contract 99999 found."),
        },
    )
    @action(detail=False, methods=["get"])
    def lookup(self, request: Request) -> Response:
        """R31: digits, `D` and `-` resolve to the contract; otherwise 404."""
        typed = request.query_params.get("number", "").strip()
        contract = lookup_contract(self.get_queryset(), typed)
        if contract is None:
            raise NotFound(f"No contract {typed} found.")
        return Response({"id": contract.pk})

    @extend_schema(
        summary="Live pricing for the contract form",
        parameters=[PricingQuerySerializer],
        responses=PricingResponse,
    )
    @action(detail=False, methods=["get"])
    def pricing(self, request: Request) -> Response:
        """R11/R12 for unsaved form values, so React never computes payment status."""
        query = PricingQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        if data.get("total_price") is None:
            return Response({"balance_due": None, "payment_status": "—", "payment_tone": "none"})
        preview = Contract(
            status=data.get("status", Contract.Status.BOOKED),
            total_price=data["total_price"],
            deposit_required=data.get("deposit_required") or 0,
            total_paid=data.get("total_paid") or 0,
        )
        return Response(
            {
                "balance_due": f"{preview.balance_due:.2f}",
                "payment_status": preview.payment_status,
                "payment_tone": preview.payment_tone,
            }
        )
