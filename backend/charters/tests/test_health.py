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


@pytest.mark.django_db
def test_schema_lists_booking_endpoints(client):
    import yaml

    paths = yaml.safe_load(client.get(reverse("schema")).content)["paths"]
    for path in [
        "/api/contracts/",
        "/api/contracts/{id}/",
        "/api/contracts/next-number/",
        "/api/contracts/lookup/",
        "/api/contracts/pricing/",
        "/api/reference/",
        "/api/zip/{zip_code}/",
    ]:
        assert path in paths
