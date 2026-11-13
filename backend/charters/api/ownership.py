"""Sandbox isolation, implemented once (docs/DEMO_SANDBOX.md, CLAUDE.md rule 1).

Every viewset for a visitor-owned model (Contract, TripUnit) inherits from
`OwnedModelViewSet`. Every serializer field that points at an owned row uses
`OwnedPrimaryKeyRelatedField`. Another owner's row then simply does not exist
for the request: 404 on detail routes and actions, "does not exist" on input.
"""

from django.db import models
from rest_framework import mixins, serializers, viewsets


def owned(model: type[models.Model], user) -> models.QuerySet:
    """The rows of `model` that belong to `user` (none for an anonymous user)."""
    if not getattr(user, "is_authenticated", False):
        return model.objects.none()
    return model.objects.filter(owner=user)


class OwnedGenericViewSet(viewsets.GenericViewSet):
    """GenericViewSet scoped to `request.user`.

    Subclasses set `model` instead of `queryset`, so there is no unfiltered
    queryset to forget about. To add select_related and so on, override
    `get_queryset` and start from `super().get_queryset()`.
    """

    model: type[models.Model]

    def get_queryset(self) -> models.QuerySet:
        return owned(self.model, self.request.user)

    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)


class OwnedModelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    OwnedGenericViewSet,
):
    """Full CRUD, scoped to `request.user`. Pick mixins on OwnedGenericViewSet for less."""

    def perform_create(self, serializer) -> None:
        # Restated: CreateModelMixin comes first in the MRO and would otherwise win.
        serializer.save(owner=self.request.user)


class OwnedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """A primary-key field that only accepts rows owned by the requesting user."""

    def __init__(self, model: type[models.Model], **kwargs):
        self.model = model
        super().__init__(**kwargs)

    def get_queryset(self) -> models.QuerySet:
        request = self.context.get("request")
        return owned(self.model, getattr(request, "user", None))
