from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views
from .board import UnitViewSet, board_export, board_view, bus_board_view
from .contracts import ContractViewSet

router = SimpleRouter()
router.register("contracts", ContractViewSet, basename="contract")
router.register("units", UnitViewSet, basename="unit")

urlpatterns = [
    path("health/", views.health, name="health"),
    path("demo-login/", views.demo_login, name="demo-login"),
    path("session/", views.session, name="session"),
    path("logout/", views.logout_view, name="logout"),
    path("reference/", views.reference, name="reference"),
    path("zip/<str:zip_code>/", views.zip_lookup, name="zip"),
    path("board/", board_view, name="board"),
    path("board/export.xlsx", board_export, name="board-export"),
    path("buses/board/", bus_board_view, name="bus-board"),
    path("", include(router.urls)),
]
