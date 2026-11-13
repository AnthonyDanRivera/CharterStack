import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from charters.models import Bus, Driver, Terminal, ZipCode


@pytest.mark.django_db
def test_seed_reference_loads_all_reference_data():
    call_command("seed_reference")
    assert list(Terminal.objects.values_list("code", flat=True)) == ["CT", "MA", "NJ", "NY", "PA"]
    assert Driver.objects.count() == 10
    assert Bus.objects.count() == 8
    assert ZipCode.objects.count() == 39
    assert list(Bus.objects.filter(has_wc_lift=True).values_list("number", flat=True)) == ["4533"]
    hoboken = ZipCode.objects.get(zip="07030")
    assert (hoboken.city, hoboken.state, hoboken.county) == ("Hoboken", "NJ", "Hudson County")


@pytest.mark.django_db
def test_seed_reference_is_idempotent():
    call_command("seed_reference")
    Driver.objects.filter(name="Marcus Bell").update(phone="changed")
    call_command("seed_reference")
    assert Driver.objects.count() == 10
    assert Terminal.objects.count() == 5
    assert Driver.objects.get(name="Marcus Bell").phone == "(201) 555-0181"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("model", "expected"),
    [("terminal", "New Jersey"), ("driver", "Marcus Bell"), ("bus", "MCI J4500")],
)
def test_admin_lists_reference_data_after_seeding(client, model, expected):
    call_command("seed_reference")
    admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
    client.force_login(admin)
    response = client.get(reverse(f"admin:charters_{model}_changelist"))
    assert response.status_code == 200
    assert expected in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("model", ["zipcode", "contract", "tripunit"])
def test_admin_registers_other_models(client, model):
    admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
    client.force_login(admin)
    assert client.get(reverse(f"admin:charters_{model}_changelist")).status_code == 200
