"""Test-only endpoints that exercise OwnedModelViewSet on every kind of route.

The real contract and unit endpoints arrive in Phases 3-4 and are added to
test_isolation.py as they land. These prove the base class itself: list, detail,
update, delete, create and a custom detail action.
"""

from django.db.models import Max
from django.urls import include, path
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter

from charters.api.ownership import OwnedModelViewSet, OwnedPrimaryKeyRelatedField
from charters.models import Contract, Terminal, TripUnit


class ContractSerializer(serializers.ModelSerializer):
    terminal = serializers.SlugRelatedField(slug_field="code", queryset=Terminal.objects.all())

    class Meta:
        model = Contract
        exclude = ["owner"]


class UnitSerializer(serializers.ModelSerializer):
    contract = OwnedPrimaryKeyRelatedField(Contract)

    class Meta:
        model = TripUnit
        fields = ["id", "contract", "unit_number", "is_duplicate", "dispatch_notes"]


class ContractViewSet(OwnedModelViewSet):
    model = Contract
    serializer_class = ContractSerializer


class UnitViewSet(OwnedModelViewSet):
    model = TripUnit
    serializer_class = UnitSerializer

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        unit = self.get_object()
        last = unit.contract.units.filter(is_duplicate=True).aggregate(n=Max("unit_number"))["n"]
        dup = TripUnit.objects.create(
            owner=request.user,
            contract=unit.contract,
            is_duplicate=True,
            unit_number=(last or 0) + 1,
        )
        return Response(UnitSerializer(dup).data, status=status.HTTP_201_CREATED)


router = SimpleRouter()
router.register("contracts", ContractViewSet, basename="t-contract")
router.register("units", UnitViewSet, basename="t-unit")

urlpatterns = [path("api/", include("charters.api.urls")), path("t/", include(router.urls))]
