from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("demo-login/", views.demo_login, name="demo-login"),
    path("session/", views.session, name="session"),
    path("logout/", views.logout_view, name="logout"),
]
