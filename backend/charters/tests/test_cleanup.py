"""cleanup_demo deletes only expired demo users (docs/DEMO_SANDBOX.md)."""

import datetime as dt

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from charters.models import Bus, Contract, DemoSession, Driver, Terminal, TripUnit, ZipCode
from charters.services import cleanup_demo, seed_sandbox
from charters.timeutil import resolve_timezone

User = get_user_model()


def make_demo(username: str, hours_old: float, **user_fields):
    user = User.objects.create_user(username=username, **user_fields)
    DemoSession.objects.create(
        user=user,
        short_id=username.upper().replace("_", "-")[:10],
        created_at=timezone.now() - dt.timedelta(hours=hours_old),
    )
    seed_sandbox(user, today=dt.date(2026, 11, 12), tz=resolve_timezone(None))
    return user


@pytest.mark.django_db
def test_cleanup_deletes_expired_demo_user_and_sandbox(reference):
    old = make_demo("demo_old01", hours_old=25)
    assert cleanup_demo() == 1
    assert not User.objects.filter(pk=old.pk).exists()
    assert not Contract.objects.filter(owner_id=old.pk).exists()
    assert not TripUnit.objects.filter(owner_id=old.pk).exists()
    assert not DemoSession.objects.exists()


@pytest.mark.django_db
def test_cleanup_keeps_fresh_demo_users(reference):
    fresh = make_demo("demo_new01", hours_old=23)
    assert cleanup_demo() == 0
    assert Contract.objects.filter(owner=fresh).count() == 12


@pytest.mark.django_db
def test_cleanup_never_touches_superusers_staff_or_plain_users(reference):
    make_demo("demo_root1", hours_old=48, is_superuser=True, is_staff=True)
    make_demo("demo_staff", hours_old=48, is_staff=True)
    make_demo("visitor_01", hours_old=48)  # has a DemoSession but not the demo_ prefix
    User.objects.create_user(username="demo_nosess")  # prefix but no DemoSession
    User.objects.create_superuser("admin", "admin@example.com", "pw")
    assert cleanup_demo() == 0
    assert User.objects.count() == 5


@pytest.mark.django_db
def test_cleanup_never_touches_reference_data(reference):
    make_demo("demo_old02", hours_old=30)
    cleanup_demo()
    counts = [m.objects.count() for m in (Terminal, Driver, Bus, ZipCode)]
    assert counts == [5, 10, 8, 39]


@pytest.mark.django_db
def test_cleanup_demo_command(reference, capsys):
    make_demo("demo_old03", hours_old=30)
    make_demo("demo_new03", hours_old=1)
    call_command("cleanup_demo")
    assert "Deleted 1 expired demo sandbox(es)." in capsys.readouterr().out
    assert list(User.objects.values_list("username", flat=True)) == ["demo_new03"]
