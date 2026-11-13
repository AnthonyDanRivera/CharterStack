"""Demo login, session and logout (docs/API.md, docs/DEMO_SANDBOX.md)."""

import datetime as dt
import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from charters.models import Contract, DemoSession, TripUnit


@pytest.mark.django_db
def test_session_is_401_before_login(client):
    response = client.get("/api/session/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_demo_login_creates_user_session_and_sandbox(client, reference):
    response = client.post("/api/demo-login/")
    assert response.status_code == 201
    body = response.json()
    assert body["user"] == "Demo User"
    assert body["server"] == "demo-server"
    assert re.fullmatch(r"DEMO-[A-Z0-9]{5}", body["session_id"])

    user = get_user_model().objects.get(demo_session__short_id=body["session_id"])
    assert user.username == "demo_" + body["session_id"][5:].lower()
    assert not user.has_usable_password()
    assert not user.is_staff and not user.is_superuser
    assert Contract.objects.filter(owner=user).count() == 12
    assert TripUnit.objects.filter(owner=user).count() == 13


@pytest.mark.django_db
def test_session_returns_same_object_after_login(client, reference):
    login = client.post("/api/demo-login/").json()
    response = client.get("/api/session/")
    assert response.status_code == 200
    assert response.json() == login


@pytest.mark.django_db
def test_demo_login_again_resumes_the_same_sandbox(client, reference):
    first = client.post("/api/demo-login/").json()
    again = client.post("/api/demo-login/")
    assert again.status_code == 200
    assert again.json()["session_id"] == first["session_id"]
    assert DemoSession.objects.count() == 1


@pytest.mark.django_db
def test_two_browsers_get_two_sandboxes(demo_client):
    a = demo_client().get("/api/session/").json()["session_id"]
    b = demo_client().get("/api/session/").json()["session_id"]
    assert a != b
    assert Contract.objects.count() == 24


@pytest.mark.django_db
def test_logout_ends_session_and_keeps_sandbox(demo_client):
    client = demo_client()
    assert client.post("/api/logout/").status_code == 204
    assert client.get("/api/session/").status_code == 401
    assert Contract.objects.count() == 12  # left for cleanup_demo


@pytest.mark.django_db
def test_started_at_uses_visitor_time_zone(reference):
    client = Client(headers={"X-Timezone": "Asia/Tokyo"})
    started = client.post("/api/demo-login/").json()["started_at"]
    assert started.endswith("+09:00")
    assert dt.datetime.fromisoformat(started).tzinfo is not None


@pytest.mark.django_db
def test_unknown_time_zone_falls_back_to_new_york(reference):
    client = Client(headers={"X-Timezone": "Not/AZone"})
    started = client.post("/api/demo-login/").json()["started_at"]
    assert started[-6:] in {"-05:00", "-04:00"}


@pytest.mark.django_db
def test_session_cookie_lasts_24_hours(client, reference):
    client.post("/api/demo-login/")
    assert client.session.get_expiry_age() == 24 * 60 * 60


@pytest.mark.django_db
def test_demo_login_requires_csrf_token(reference):
    client = Client(enforce_csrf_checks=True)
    assert client.post("/api/demo-login/").status_code == 403

    client.get("/api/session/")  # sets the csrftoken cookie
    token = client.cookies["csrftoken"].value
    response = client.post("/api/demo-login/", headers={"X-CSRFToken": token})
    assert response.status_code == 201


@pytest.mark.django_db
def test_demo_login_throttled_to_five_per_hour_per_ip(reference):
    statuses = [Client().post("/api/demo-login/").status_code for _ in range(6)]
    assert statuses == [201] * 5 + [429]
    assert DemoSession.objects.count() == 5


@pytest.mark.django_db
def test_health_is_not_throttled(client):
    assert all(client.get("/api/health/").status_code == 200 for _ in range(35))


@pytest.mark.django_db
def test_anonymous_requests_throttled_at_30_per_minute(client):
    statuses = [client.get("/api/session/").status_code for _ in range(31)]
    assert statuses[:30] == [401] * 30
    assert statuses[30] == 429
