from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views
from .contracts import ContractViewSet

router = SimpleRouter()
router.register("contracts", ContractViewSet, basename="contract")

urlpatterns = [
    path("health/", views.health, name="health"),
    path("demo-login/", views.demo_login, name="demo-login"),
    path("session/", views.session, name="session"),
    path("logout/", views.logout_view, name="logout"),
    path("reference/", views.reference, name="reference"),
    path("zip/<str:zip_code>/", views.zip_lookup, name="zip"),
    path("", include(router.urls)),
]
