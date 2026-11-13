import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_returns_ok_without_login(client):
    response = client.get(reverse("health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_api_docs_page_loads(client):
    assert client.get(reverse("swagger-ui")).status_code == 200
    assert client.get(reverse("schema")).status_code == 200
